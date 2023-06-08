import logging
from typing import Any

import apscheduler.job
import requests
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for, make_response
from ichrisbirch import schemas
from ichrisbirch.config import get_settings
from ichrisbirch.models.autotask import TaskFrequency
from ichrisbirch.models.task import TaskCategory
from ichrisbirch.app.routes.tasks import TASKS_URL
from ichrisbirch.wsgi import scheduler
import copy

settings = get_settings()
blueprint = Blueprint('autotasks', __name__, template_folder='templates/autotasks', static_folder='static')

logger = logging.getLogger(__name__)

AUTOTASKS_URL = f'{settings.api_url}/autotasks'
TASK_FREQUENCIES = [t.value for t in TaskFrequency]
TASK_CATEGORIES = [t.value for t in TaskCategory]
TIMEOUT = settings.request_timeout


def task_create_post_request(data: dict):
    """Thin wrapper around `requests.post` for error handling and calling a single function from the scheduler"""
    response = requests.post(TASKS_URL + '/crud/', data=data, timeout=TIMEOUT)
    logger.debug(response.text)
    if response.status_code == 201:
        flash(f'Autotask scheduled: {data.get("name")}', 'success')
    else:
        error_message = f'{response.url} : {response.status_code} {response.reason}'
        logger.error(error_message)
        flash(error_message, 'error')


def convert_autotask_frequency_to_trigger_args(frequency: TaskFrequency):
    mapping = {
        TaskFrequency.Daily: {'days': 1},
        TaskFrequency.Weekly: {'weeks': 1},
        TaskFrequency.Biweekly: {'weeks': 2},
        TaskFrequency.Monthly: {'months': 1},
        TaskFrequency.Quarterly: {'months': 3},
        TaskFrequency.Semiannual: {'months': 6},
        TaskFrequency.Yearly: {'years': 1},
    }
    return mapping.get(frequency)


def add_autotask_job_to_scheduler(autotask: schemas.AutoTask, jobstore='ichrisbirch') -> apscheduler.job.Job:
    """Adds an autotask to the scheduler

    Returns: apscheduler.job.Job
    """
    task = schemas.Task(**autotask.dict().pop('method'))
    return scheduler.add_job(
        func=task_create_post_request,
        trigger='interval',
        trigger_args=convert_autotask_frequency_to_trigger_args(autotask.frequency),
        args=None,
        kwargs=task.dict(),
        id=task.id,
        name=task.name,
        jobstore=jobstore,
    )


@blueprint.route('/', methods=['GET'])
def index():
    """Autotasks home endpoint"""
    response = requests.get(AUTOTASKS_URL, timeout=TIMEOUT)
    if response.status_code == 200:
        autotasks = [schemas.AutoTask(**task) for task in response.json()]
    else:
        error_message = f'{response.url} : {response.status_code} {response.reason}'
        logger.error(error_message)
        flash(error_message, 'error')
        autotasks = []

    return render_template(
        'autotasks/index.html', autotasks=autotasks, task_categories=TASK_CATEGORIES, task_frequencies=TASK_FREQUENCIES
    )


@blueprint.route('/crud/', methods=['POST'])
def crud():
    """CRUD endpoint for autotasks"""
    data: dict[str, Any] = request.form.to_dict()
    method = data.pop('method')
    logger.debug(f'{request.referrer=}')
    logger.debug(f'{method=}')
    logger.debug(f'{data=}')
    match method:

        case 'add':
            # 1. Validate and send the form data to the autotasks API.
            # 2. If successful, send task as args to the scheduler that will posts those task args
            #    to the tasks API create endpoint on the specified schedule.
            autotask = schemas.AutoTaskCreate(**data)
            response = requests.post(AUTOTASKS_URL, data=autotask.json(), timeout=TIMEOUT)
            logger.debug(response.text)
            if response.status_code != 201:
                error_message = f'{response.url} : {response.status_code} {response.reason}'
                logger.error(error_message)
                flash(error_message, 'error')
            else:
                try:
                    add_autotask_job_to_scheduler(schemas.AutoTask(**response.json()))
                except Exception as e:
                    message = f'Autotask Scheduling Failed: {e}'
                    logger.error(message)
                    flash(message, 'error')
                    delete = requests.delete(f'{AUTOTASKS_URL}/{response.json().get("id")}', timeout=TIMEOUT)
                    logger.debug(delete.text)
                    if delete.status_code != 204:
                        error_message = f'{delete.url} : {delete.status_code} {delete.reason}'
                        logger.error(error_message)
                        flash(error_message, 'error')
                else:
                    flash(f'Autotask Added: {data.get("name")}', 'success')
            return redirect(request.referrer or url_for('autotasks.index'))

        case 'delete':
            autotask_id = data.get('id')
            response = requests.delete(f'{AUTOTASKS_URL}/{autotask_id}', timeout=TIMEOUT)
            logger.debug(response.text)
            if response.status_code != 204:
                error_message = f'{response.url} : {response.status_code} {response.reason}'
                logger.error(error_message)
                flash(error_message, 'error')
            else:
                try:
                    scheduler.remove_job(autotask_id)
                except Exception as e:
                    message = f'Autotask Schedule Removal Failed: {e}'
                    logger.error(message)
                    flash(message, 'error')
                else:
                    flash(f'Autotask deleted: {data.get("name")}', 'success')
            return redirect(request.referrer or url_for('autotasks.index'))

    return abort(405, description=f"Method {method} not accepted")
