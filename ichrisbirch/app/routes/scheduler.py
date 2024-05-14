import logging

import pendulum
from apscheduler.job import Job
from fastapi import status
from flask import Blueprint
from flask import flash
from flask import render_template
from flask import request

from ichrisbirch.config import get_settings
from ichrisbirch.scheduler.main import get_jobstore

settings = get_settings()
logger = logging.getLogger('app.scheduler')
blueprint = Blueprint('scheduler', __name__, template_folder='templates/scheduler', static_folder='static')


def calculate_time_until_next_runs(jobs: list[Job]) -> list[str]:
    time_until_next_runs = []
    for job in jobs:
        if job.next_run_time:
            next_run = pendulum.interval(pendulum.now(job.next_run_time.tzinfo), job.next_run_time).in_words()
        else:
            next_run = 'Paused'
        time_until_next_runs.append(next_run)
    return time_until_next_runs


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    jobstore = get_jobstore(settings=settings)
    if request.method == 'POST':
        data = request.form.to_dict()
        job_id = data.get('job_id')
        action = data.pop('action')
        if job := jobstore.lookup_job(job_id):
            match action:
                case 'pause_job':
                    job.next_run_time = None
                    jobstore.update_job(job)
                    flash(f'Job: {job_id} paused', 'success')
                case 'resume_job':
                    job.next_run_time = job.trigger.get_next_fire_time(None, pendulum.now())
                    jobstore.update_job(job)
                    flash(f'Job: {job_id} resumed', 'success')
                case 'delete_job':
                    jobstore.remove_job(job_id)
                    flash(f'Job: {job_id} deleted', 'success')
                case _:
                    message = f"{status.HTTP_405_METHOD_NOT_ALLOWED}: Method/Action '{action}' not allowed"
                    flash(message, 'error')
                    logger.error(message)
        else:
            message = f'Job: {job_id} not found'
            flash(message, 'error')
            logger.error(message)

    jobs = jobstore.get_all_jobs()
    time_until_next_runs = calculate_time_until_next_runs(jobs)
    return render_template('scheduler/index.html', jobs=jobs, time_until_next_runs=time_until_next_runs, zip=zip)
