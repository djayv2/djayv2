import subprocess
from logging_setup import get_logger
import os
from joblib import Parallel, delayed
from croniter import croniter
from datetime import datetime, timezone
import json


RUN_ALL = os.getenv("RUN_ALL")
ADHOC_SCRIPTS = os.getenv("ADHOC_SCRIPTS")

ENV_NAME = os.getenv("ENV_NAME", "local")

# Set up logging
logger = get_logger(__name__)


def run_script(script_path):
    base_directory = os.path.dirname(os.path.abspath(__file__))
    try:
        full_script_path = os.path.join(base_directory, script_path)
        subprocess.run(["python", full_script_path], cwd=base_directory, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running script {script_path}: {e}")
        print(e)


with open("run_jobs.json") as f:
    jobs = json.load(f)


if ADHOC_SCRIPTS == "None":
    para_jobs = []
    non_para_jobs = []
    for job in jobs:
        if croniter.match(jobs[job]["schedule"], datetime.now(timezone.utc)):
            if jobs[job]["size"] == "small":
                para_jobs.append(jobs[job]["path_to_job"])
            else:
                non_para_jobs.append(jobs[job]["path_to_job"])
    Parallel(n_jobs=-1, backend="threading")(
        delayed(run_script)(script) for script in para_jobs
    )
    for script in non_para_jobs:
        run_script(script)

else:
    logger.warning(
        f"Running adhoc scripts for {ENV_NAME}: {ADHOC_SCRIPTS}"
    )
    adhoc_scripts = os.getenv("ADHOC_SCRIPTS").split(",")
    Parallel(n_jobs=-1, backend="threading")(
        delayed(run_script)(script) for script in adhoc_scripts
    )