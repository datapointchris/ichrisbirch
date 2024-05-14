import logging

import boto3
from flask import Blueprint
from flask import render_template
from flask import request

from ichrisbirch.config import get_settings

settings = get_settings()
logger = logging.getLogger('app.backups')
blueprint = Blueprint('backups', __name__, template_folder='templates/backups', static_folder='static')


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    s3 = boto3.client('s3')
    prefix = request.args.get('prefix', '')
    response = s3.list_objects_v2(Bucket=settings.aws.s3_backup_bucket, Prefix=prefix, Delimiter='/')

    contents = response.get('Contents', [])
    files = [content.get('Key') for content in contents if 'Key' in content]

    common_prefixes = response.get('CommonPrefixes', [])
    folders = [prefix.get('Prefix') for prefix in common_prefixes]

    return render_template('backups/index.html', folders=folders, files=files, prefix=prefix)
