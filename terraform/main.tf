terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
  backend "gcs" {
    region = ""
    key    = "terraform.tfstate"  
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

resource "google_secret_manager_secret" "sender_password" {
  secret_id = "sender-password"
  
  replication {
    user_managed {
      replicas {
        location = "us-west1"
      }
    }
  }
}

resource "google_secret_manager_secret_version" "sender_password_version" {
  secret = google_secret_manager_secret.sender_password.name
  secret_data = "${var.sender_password}"
}

# Create service account for Cloud Run
resource "google_service_account" "cloud_run_sa" {
  account_id   = "cloud-run-sa"
  display_name = "Service Account for Cloud Run Job"
}

resource "google_project_iam_custom_role" "storage_secrets_role" {
  role_id     = "storageSecretsRole"
  title       = "Storage and Secrets Manager Access Role"
  description = "Custom role for GCS and Secrets Manager access"
  permissions = [
    # GCS permissions
    "storage.objects.get",
    "storage.objects.list",
    "storage.objects.create",
    "storage.objects.update",
    "storage.buckets.get",
    "storage.buckets.list",
    
    # Secrets Manager permissions
    "secretmanager.secrets.get",
    "secretmanager.secrets.list",
    "secretmanager.versions.access",
    "secretmanager.versions.get",
    "secretmanager.versions.list",
  ]
}

# Bind the custom role to the service account
resource "google_project_iam_binding" "role_binding" {
  project = var.gcp_project_id
  role    = google_project_iam_custom_role.storage_secrets_role.id
  
  members = [
    "serviceAccount:${google_service_account.cloud_run_sa.email}"
  ]
}

# Define Cloud Run service with image and secret reference
resource "google_cloud_run_v2_job" "job_posting_analyzer" {
  name     = "job-posting-analyzer"
  location = "us-west1" 

  template {
    template {
      service_account = google_service_account.cloud_run_sa.email
      max_retries = 3
      timeout = "3600s"
      
      containers {
        image = var.job_posting_analyzer_image
        args = [
          "--config",
          var.job_posting_analyzer_config
        ]
      }
    }
  }
}

# Create a service account for the Cloud Scheduler
resource "google_service_account" "scheduler_service_account" {
  account_id   = "cloud-run-scheduler-sa"
  display_name = "Cloud Run Scheduler Service Account"
}

# Grant the necessary permissions to the scheduler service account
resource "google_project_iam_member" "scheduler_role" {
  project = var.gcp_project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.scheduler_service_account.email}"
}

# Create the Cloud Scheduler job
resource "google_cloud_scheduler_job" "job" {
  name             = "cloud-run-scheduler"
  description      = "Triggers Cloud Run Job daily at 8am"
  schedule         = "0 8 * * *"
  time_zone        = "America/Los_Angeles"
  region           = var.gcp_region
  attempt_deadline = "320s"

  http_target {
    http_method = "POST"
    uri         = "https://${var.gcp_region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.gcp_project_id}/jobs/${google_cloud_run_v2_job.job_posting_analyzer.name}:run"
    headers = {
      "Content-Type" = "application/json"
      "User-Agent"   = "Google-Cloud-Scheduler"
    }
    oauth_token {
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
      service_account_email = google_service_account.scheduler_service_account.email
    }
  }
}