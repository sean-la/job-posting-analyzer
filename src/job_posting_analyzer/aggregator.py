import logging
import requests
import os
import asyncio
import argparse
import json
import google.auth
import PyPDF2

from urllib.request import urlopen
from bs4 import BeautifulSoup
from google.oauth2 import id_token
from langchain_google_genai import ChatGoogleGenerativeAI
from asynciolimiter import Limiter
from google.cloud import storage

from analyzer import JobFitAnalyzer, JobDuplicateRemover
from mail import send_email


def setup_parser():
    parser = argparse.ArgumentParser(description='Description of your program')

    parser.add_argument("--resume", type=str, required=True, help="path to resume")
    parser.add_argument("--config", type=str, required=True, help="path to config")
    parser.add_argument("--ignore_job_id", action="store_true", default=False, help="")
    
    return parser


def parse_pdf(file_path):
    """Extract text from PDF file."""
    text = ""
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    return text.strip()


def parse_html(url):
    page = urlopen(url)
    html = page.read()
    soup = BeautifulSoup(html, features="html.parser")
    text = soup.get_text().replace("\n", "  ")
    return text


def create_summary(jobs):
    summary = ""
    for job in jobs:
        summary += (f"Job: {job["title"]}\n")
        summary += (f"Company: {job["company"]["display_name"]}\n")
        summary += (f"Date posted: {job["created"]}\n")
        summary += (f"URL: {job["redirect_url"]}\n")
        summary += ("\n")
    return summary



class JobDuplicateRemoverWrapper():

    def __init__(self, model="gemini-1.5-pro"):
        llm = ChatGoogleGenerativeAI(model=model)
        self._duplicate_remover = JobDuplicateRemover(llm)

    def remove_duplicates(self, job_list: str):
        return self._duplicate_remover.remove_job_duplicates(job_list)



class JobFitAnalyzerWrapper():

    def __init__(self, model="gemini-1.5-pro", **kwargs):
        # Create an instance of the LLM, using the 'gemini-pro' model 
        llm = ChatGoogleGenerativeAI(model=model)
        self._analyzer = JobFitAnalyzer(llm)


    async def analyze(self, job_description, resume):
        analysis = self._analyzer.analyze_fit(job_description, resume)
        return analysis


class JobBoard:

    def __init__(self, job_board_api_url):
        self._api_url = job_board_api_url


    def get_jobs(self, api_parameters, **kwargs):
        """
        Fetches job postings from the Adzuna API for Canada.

        Args:
          app_id: Your Adzuna API application ID.
          app_key: Your Adzuna API application key.
          keywords: Keywords to search for in job postings.
          location: Location to search for jobs (optional).
          results_per_page: Number of results to retrieve per page.

        Returns:
          A list of dictionaries, where each dictionary represents a job posting.
        """

        try:
            response = requests.get(self._api_url, params=api_parameters)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()
            return data["results"]
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching data from Adzuna API: {e}")
            raise e


class JobFilter:

    def __init__(self, job_id_dir="/var/tmp/jobs", ignore_job_id=False, bucket=None,
                 **kwargs):
        self._job_id_dir = job_id_dir
        self._bucket = bucket
        self._filter_rules = [
            lambda job, analysis: analysis.remote_in_canada,
            lambda job, analysis: analysis.overall_match_percentage > 80,
        ]
        self._ignore_job_id = ignore_job_id


    def _job_exists_local(self, job_id):
        job_id_path = f"{self._job_id_dir}/{job_id}"
        if self._ignore_job_id:
            return False
        if not os.path.exists(job_id_path):
            content = ""
            with open(job_id_path, 'w') as f:
                f.write(content)
            return False
        else:
            return True


    def _job_exists_gcs(self, job_id):
        storage_client = storage.Client()
        bucket = storage_client.bucket(self._bucket)
        object_name = f"{self._job_id_dir}/{job_id}"
        blob = bucket.blob(object_name)
        if not blob.exists():
            blob.upload_from_string("")
            return False
        else:
            return True


    def _job_exists(self, job):
        job_id = job["id"]
        if self._bucket is not None and len(self._bucket) > 0:
            return self._job_exists_gcs(job_id)
        else:
            return self._job_exists_local(job_id)


    def filter_jobs(self, jobs, analyses):
        filtered_jobs = [
            job
            for job, analysis in zip(jobs, analyses)
            if analysis is not None and not self._job_exists(job) and all([
                filter_rule(job, analysis)
                for filter_rule in self._filter_rules
            ])
        ]
        return filtered_jobs



async def main():
    parser = setup_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )

    resume = parse_pdf(args.resume)

    with open(args.config, 'r') as f:
        config = json.load(f)

    logging.info("Retrieving jobs...")
    job_board_configs = config["job_boards"]
    job_descriptions = []

    for job_board_config in job_board_configs:
        job_board = JobBoard(job_board_config["job_board_api_url"])
        jobs = job_board.get_jobs(job_board_config["job_board_api_params"])

        logging.debug(f"Got {len(jobs)} jobs")

        for job in jobs:
            url = job["redirect_url"]
            job_description = parse_html(url)
            job_descriptions.append(job_description)

    logging.info(f"Retrieved {len(job_descriptions)} jobs.")

    job_analyzer = JobFitAnalyzerWrapper(**config)
    rate_limiter = Limiter(float(config["model_requests_per_second"]))

    analysis_jobs = [
        rate_limiter.wrap(job_analyzer.analyze(job_description, resume))
        for job_description in job_descriptions
    ]
    logging.info("Analyzing job descriptions...")
    analyses = await asyncio.gather(*analysis_jobs)
    logging.info("Done analyzing jobs descriptions.")

    job_filter = JobFilter(**config)
    logging.info("Filtering jobs...")
    filtered_jobs = job_filter.filter_jobs(jobs, analyses)
    logging.info(f"After filtering, {len(filtered_jobs)} jobs remain.")

    job_list_summary = create_summary(filtered_jobs)

    body = f"Here is your daily jobs list.\n\n{job_list_summary}"

    logging.info("Emailing job summary...")
    send_email(
        subject="Your Daily Jobs",
        body=body,
        **config
    )
    logging.info("Done emailing job summary.")


if __name__ == "__main__":
    asyncio.run(main())

