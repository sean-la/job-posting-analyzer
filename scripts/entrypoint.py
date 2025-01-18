import argparse
import logging
import asyncio

from asynciolimiter import Limiter

from job_posting_analyzer.aggregator import (
    retrieve_env_variable_or_secret,
    read_config,
    read_pdf,
    parse_html,
    create_summary,
    JobBoard,
    JobFilter,
    JobFitAnalyzerWrapper
)
from job_posting_analyzer.mail import send_email


def setup_parser():
    parser = argparse.ArgumentParser(description='Description of your program')

    parser.add_argument("--config", type=str, required=True, help="path to config")
    parser.add_argument("--resume", type=str, required=False, help="path to resume")
    parser.add_argument("--ignore_job_id", action="store_true", default=False, help="")
    parser.add_argument("--loglevel", type=str, choices=["INFO", "DEBUG"], default="INFO",
                        help="logging level")
    
    return parser


async def main():
    parser = setup_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=args.loglevel,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )

    config = read_config(args.config)

    if "sender_password" not in config:
        config["sender_password"] = retrieve_env_variable_or_secret(
            env_variable="SENDER_PASSWORD",
            secret_name="sender-password",
            project_id=config["project_id"]
        )

    if args.resume:
        config["resume"] = args.resume
    
    logging.info("Retrieving jobs...")
    job_board_configs = config["job_boards"]
    jobs = []
    job_descriptions = []

    for job_board_config in job_board_configs:
        api_url = job_board_config["job_board_api_url"]
        job_board = JobBoard(api_url)
        job_board_jobs = job_board.get_jobs(job_board_config["job_board_api_params"])

        logging.info(f"Got {len(job_board_jobs)} jobs from {api_url}.")

        for job in job_board_jobs:
            url = job["redirect_url"]
            try:
                job_description = parse_html(url)
                job_descriptions.append(job_description)
                jobs.append(job)
            except:
                pass

    num_retrieved_jobs = len(job_descriptions)
    logging.info(f"Retrieved {len(job_descriptions)} jobs.")

    job_analyzer = JobFitAnalyzerWrapper(**config)
    rate_limiter = Limiter(float(config["model_requests_per_second"]))

    resume = read_pdf(config["resume"])
    job_preferences = config["job_preferences"]

    analysis_jobs = [
        rate_limiter.wrap(job_analyzer.analyze(job_description, job_preferences, resume))
        for job_description in job_descriptions
    ]
    logging.info("Analyzing job descriptions...")
    analyses = await asyncio.gather(*analysis_jobs)
    logging.info("Done analyzing jobs descriptions.")

    if len(analyses) != len(job_descriptions):
        raise Exception(
            f"{len(analyses)} analyses returned, but " \
            + f"{len(job_descriptions)} jobs were given."
        )

    job_filter = JobFilter(
        ignore_job_id=args.ignore_job_id,
        **config
    )
    logging.info("Filtering jobs...")
    filtered_jobs = job_filter.filter_jobs(jobs, analyses)

    num_filtered_jobs = len(filtered_jobs)
    logging.info(f"After filtering, {len(filtered_jobs)} jobs remain.")

    job_list_summary = create_summary(filtered_jobs)

    body = f"Here is your daily jobs list. {num_filtered_jobs}/{num_retrieved_jobs} jobs remained after filtering.\n\n{job_list_summary}"

    logging.info("Emailing job summary...")
    send_email(
        subject="Your Daily Jobs",
        body=body,
        **config
    )
    logging.info("Done emailing job summary.")



if __name__ == "__main__":
    asyncio.run(main())

