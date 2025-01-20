# LLM-Powered Job Posting Analyzer

Looking for a job? Use my LLM-powered job posting analyzer to automatically analyze job postings
from websites like Adzuna, compare them to your resume and job preferences, and email you jobs
that AI thinks you'd be a great fit for!

You can run this locally, but you can also deploy this into Google Cloud Platform for free!

**Table of Contents**

- [Installation](#installation)
- [Usage](#usage)

## Installation

### Setup environment

The Docker image will send you an email using Gmail's API.
You'll need to provide it your password, which the image will read
from an environment variable `SENDER_PASSWORD` or in your Google Secret Manager
under the name `sender-password`.

You'll also need to setup an API key for Google Gemini under the environment variable
`GOOGLE_API_KEY`, or within Google Secret Manager under the name `google-api-key`.

Finally, specify your Google Cloud Project ID under `GOOGLE_CLOUD_PROJECT`.

Lastly, you'll also need to set up your Google Cloud application default credentials that
should be accessible under `$HOME/.config/gcloud/application_default_credentials.json`.


### Setup the config

See the example config under `data/example_config.json` to get an idea of the schema.
Here is an explanation for various fields in the config:

- `recipient_address`: The email account that will receive emails containing job recommendations.
- `sender_address`: The Gmail account that will send the emails.
- `project_id`: Optional, name of your GCS project.
- `bucket`: Optional, name of your GCS bucket.
- `resume`: Path to your resume. Can either be a local path or a GCS bucket path.
- `job_preferences`: Your job preferences.
- `overall_match_percentage`: The lower limit for match percentage for jobs.

### Building the Docker image

Build the Docker image under the image name `job-posting-analyzer:dev` using the command

```bash
./scripts/docker_build.sh
```

### Running the image

You can display help menu using command

```bash
docker run job-posting-analyzer:dev --help
```

You can also run the script `./scripts/docker_run.sh --config $CONFIG_PATH`, which will
run the Docker image locally.
See the contents of `scripts/docker_run.sh` to get an idea of the environment variables the image needs.