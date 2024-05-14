import logging
from dataclasses import dataclass
from datetime import datetime

import boto3
from flask import Blueprint
from flask import render_template
from flask import request

from ichrisbirch.app.helpers import convert_bytes
from ichrisbirch.config import get_settings

settings = get_settings()
logger = logging.getLogger('app.backups')
blueprint = Blueprint('backups', __name__, template_folder='templates/backups', static_folder='static')


@dataclass
class Backup:
    filename: str
    prefix: str
    last_modified: datetime
    _size: int

    @property
    def size(self):
        return convert_bytes(self._size)


@blueprint.route('/', methods=['GET', 'POST'])
def index():
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
        'backups/index.html', folders=folders, backups=backups, prefix=prefix, up_one_level=up_one_level
    )
