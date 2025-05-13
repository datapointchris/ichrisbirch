import logging
import traceback
from dataclasses import dataclass
from datetime import datetime

import boto3
import pendulum
import polars as pl
from apscheduler.job import Job
from fastapi import status
from flask import Blueprint
from flask import current_app
from flask import flash
from flask import render_template
from flask import request

from ichrisbirch.app import utils
from ichrisbirch.app.login import admin_login_required
from ichrisbirch.scheduler.main import get_jobstore
from ichrisbirch.util import get_logger_filename_from_handlername

logger = logging.getLogger('app.admin')
blueprint = Blueprint('admin', __name__, template_folder='templates/admin', static_folder='static')


@blueprint.before_request
@admin_login_required
def enforce_admin_login():
    pass


@blueprint.route('/', methods=['GET'])
def index():
    settings = current_app.config['SETTINGS']
    return render_template(
        'admin/serverstats.html', settings=settings, server_time=pendulum.now().isoformat(timespec='seconds')
    )


@dataclass
class Backup:
    filename: str
    prefix: str
    last_modified: datetime
    _size: int

    @property
    def size(self):
        return utils.convert_bytes(self._size)


@blueprint.route('/backups/', methods=['GET', 'POST'])
def backups():
    settings = current_app.config['SETTINGS']
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
    backups = sorted(backups, key=lambda backup: backup.last_modified, reverse=True)

    common_prefixes = response.get('CommonPrefixes', [])
    folders = [prefix.get('Prefix') for prefix in common_prefixes]

    return render_template(
        'admin/backups.html',
        backup_bucket=settings.aws.s3_backup_bucket,
        folders=folders,
        backups=backups,
        prefix=prefix,
        up_one_level=up_one_level,
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
    settings = current_app.config['SETTINGS']
    jobstore = get_jobstore(settings=settings)
    if request.method.upper() == 'POST':
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


@blueprint.route('/logs/', methods=['GET'])
def logs():
    settings = current_app.config['SETTINGS']
    return render_template('admin/logs.html', api_host=settings.fastapi.host, api_port=settings.fastapi.port)


def log_file_to_polars_df(filename: str, debug=False) -> pl.DataFrame:
    schema = {
        'log_level': pl.Categorical,
        'timestamp': pl.Datetime,
        'logger_name': pl.String,
        'func_name': pl.String,
        'lineno': pl.Int16,
        'message': pl.String,
    }
    num_errors = 0
    previous_line = ''
    errors = []
    was_error = False
    last_error = None

    def _process_log_line(line: str):
        nonlocal num_errors, previous_line, was_error, last_error
        try:
            part, message = line.strip().split('|')
            log_level, timestamp, part = part.strip().rsplit(' ', maxsplit=2)
            logger_name, func_name, lineno = part.strip().split(':')
            previous_line = line
            if was_error:
                errors.append(f'NXT LINE: {line.strip()}\n')
            was_error = False
            last_error = None
        except Exception:
            num_errors += 1
            errors.extend([traceback.format_exc(), f'PRE LINE: {previous_line.strip()}', f'ERR LINE: {line.strip()}'])
            previous_line = line
            was_error = True
            return None
        return {
            'log_level': log_level.strip('[] ').strip(),
            'timestamp': timestamp.strip(),
            'logger_name': logger_name.strip(),
            'func_name': func_name.strip(),
            'lineno': lineno.strip(),
            'message': message.strip(),
        }

    def _cast_columns(df, schema: dict):
        casts = [pl.col(k).cast(v) for k, v in schema.items()]
        return df.select(*casts)

    def _process_log_file(filename):
        with open(filename) as f:
            lines = []
            for line in f:
                if processed := _process_log_line(line):
                    lines.append(processed)
        return lines

    log_lines = _process_log_file(filename)
    df = pl.DataFrame(log_lines)
    converted = _cast_columns(df, schema)
    num_logs = len(log_lines)
    logger.info(f'processed {num_logs} logs from {filename}')
    logger.info(f'total errors while processing: {num_errors}/{num_logs} - {round(num_errors / num_logs, 4)}%')
    if debug:
        print()
        for error in errors:
            print(error)
    return converted


@dataclass
class LogChart:
    title: str
    title_element_id: str
    chart_element_id: str
    data_element_id: str
    data: list[dict]
    x_axis_key: str
    y_axis_key: str


def create_log_chart(title: str, data: pl.DataFrame, x_axis_key: str, y_axis_key: str) -> LogChart:
    camel_title = ''.join([word.capitalize() if i != 0 else word.lower() for i, word in enumerate(title.split())])
    return LogChart(
        title=title,
        title_element_id=camel_title + 'Title',
        chart_element_id=camel_title + 'Chart',
        data_element_id=camel_title,
        data=data.to_dicts(),
        x_axis_key=x_axis_key,
        y_axis_key=y_axis_key,
    )


@blueprint.route('/log-graphs/', methods=['GET', 'POST'])
def log_graphs():
    handler = 'ichrisbirch_file'
    if log_filename := get_logger_filename_from_handlername(handler):
        log_df = log_file_to_polars_df(log_filename)
    else:
        msg = f'log file: {log_filename} not found for handler: {handler}'
        flash(msg, 'error')
        logger.error(msg)

    log_count_by_level = create_log_chart(
        title='Log Count by Level',
        data=log_df.group_by('log_level').len().sort('len', descending=True),
        x_axis_key='log_level',
        y_axis_key='len',
    )

    log_count_by_day = create_log_chart(
        title='Log Count by Day',
        data=log_df.group_by(pl.col('timestamp').dt.date()).len().sort(['timestamp', 'len'], descending=True),
        x_axis_key='timestamp',
        y_axis_key='len',
    )

    log_count_errors_by_logger_name = create_log_chart(
        title='Log Count Errors by Logger Name',
        data=log_df.filter(pl.col('log_level') == 'ERROR').group_by('logger_name').len().sort('len', descending=True),
        x_axis_key='logger_name',
        y_axis_key='len',
    )

    log_count_errors_by_func_name = create_log_chart(
        title='Log Count Errors by Function Name',
        data=log_df.filter(pl.col('log_level') == 'ERROR').group_by('func_name').len().sort('len', descending=True),
        x_axis_key='func_name',
        y_axis_key='len',
    )

    log_count_warnings_by_logger_name = create_log_chart(
        title='Log Count Warnings by Logger Name',
        data=log_df.filter(pl.col('log_level') == 'WARNING').group_by('logger_name').len().sort('len', descending=True),
        x_axis_key='logger_name',
        y_axis_key='len',
    )

    log_count_warnings_by_func_name = create_log_chart(
        title='Log Count Warnings by Function Name',
        data=log_df.filter(pl.col('log_level') == 'WARNING').group_by('func_name').len().sort('len', descending=True),
        x_axis_key='func_name',
        y_axis_key='len',
    )

    # TODO: [2024/08/01] - Add stacked bar charts for compound groupings
    # log_count_logger_name_and_levels = (
    #     log_df.group_by(['logger_name', 'log_level']).len().sort('log_level', descending=True)
    # )
    # log_count_func_name_and_levels = (
    #     log_df.group_by(['func_name', 'log_level']).len().sort('log_level', descending=True)
    # )

    log_charts = [
        log_count_by_level,
        log_count_by_day,
        log_count_errors_by_logger_name,
        log_count_errors_by_func_name,
        log_count_warnings_by_logger_name,
        log_count_warnings_by_func_name,
    ]

    return render_template('admin/log_graphs.html', log_charts=log_charts)
