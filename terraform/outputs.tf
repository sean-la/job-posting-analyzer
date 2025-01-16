output "job_name" {
  value = google_cloud_run_v2_job.job_posting_analyzer.name
}

output "job_location" {
  value = google_cloud_run_v2_job.job_posting_analyzer.location
}

output "scheduler_name" {
  value = google_cloud_scheduler_job.job.name
}