import logging
from dataclasses import dataclass
from datetime import datetime

import boto3
import pendulum
from apscheduler.job import Job
from fastapi import status
from flask import Blueprint
from flask import flash
from flask import render_template
from flask import request

from ichrisbirch.app.helpers import convert_bytes
from ichrisbirch.config import get_settings
from ichrisbirch.scheduler.main import get_jobstore

settings = get_settings()
logger = logging.getLogger('app.admin')
blueprint = Blueprint('admin', __name__, template_folder='templates/admin', static_folder='static')


@blueprint.route('/', methods=['GET'])
def index():
    return render_template(
        'admin/index.html',
        settings=settings,
        server_time=pendulum.now('UTC').isoformat(),
        local_time=pendulum.now().isoformat(),
    )


@dataclass
class Backup:
    filename: str
    prefix: str
    last_modified: datetime
    _size: int

    @property
    def size(self):
        return convert_bytes(self._size)


@blueprint.route('/backups/', methods=['GET', 'POST'])
def backups():
    s3 = boto3.client('s3')
    prefix = request.args.get('prefix', '')
    up_one_level = prefix.rsplit('/', 2)[0] + '/'
    up_one_level = '' if up_one_level == prefix else up_one_level
    response = s3.list_objects_v2(Bucket=settings.aws.s3_backup_bucket, Prefix=prefix, Delimiter='/')
    contents = response.get('Contents', [])
    backups = [
        Backup(
            filename=content['Key'].split('/')[-1],
            prefix=content['Key'].split('/')[:-1],
            last_modified=content['LastModified'],
            _size=content['Size'],
        )
        for content in contents
    ]
    backups = sorted(backups, key=lambda backup: backup.filename, reverse=True)

    common_prefixes = response.get('CommonPrefixes', [])
    folders = [prefix.get('Prefix') for prefix in common_prefixes]

    return render_template(
        'admin/backups.html', folders=folders, backups=backups, prefix=prefix, up_one_level=up_one_level
    )


def calculate_time_until_next_runs(jobs: list[Job]) -> list[str]:
    time_until_next_runs = []
    for job in jobs:
        if job.next_run_time:
            next_run = pendulum.interval(pendulum.now(job.next_run_time.tzinfo), job.next_run_time).in_words()
        else:
            next_run = 'Paused'
        time_until_next_runs.append(next_run)
    return time_until_next_runs


@blueprint.route('/scheduler/', methods=['GET', 'POST'])
def scheduler():
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
    return render_template('admin/scheduler.html', jobs=jobs, time_until_next_runs=time_until_next_runs, zip=zip)
