import requests

def convert_to_raw_logs_url(job_url: str) -> str:
    # TODO: map job URL → raw artifact URL
    return job_url.replace("https://prow.ci.openshift.org/job/", "https://storage.googleapis.com/ci-op-logs/") + "/artifacts/latest/logs.txt"

async def fetch_ci_logs(job_url: str) -> str:
    raw = convert_to_raw_logs_url(job_url)
    resp = requests.get(raw)
    resp.raise_for_status()
    return resp.text