from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Blueprint, render_template

from ichrisbirch.config import settings

blueprint = Blueprint(
    'health',
    __name__,
    template_folder='templates/health',
    static_folder='static',
)


@blueprint.route('/')
def health():
    """Health and info endpoint for app"""
    return render_template(
        'health/index.html',
        settings=settings,
        version=settings.VERSION,
        server_time=datetime.now().isoformat(),
        local_time=datetime.now(tz=ZoneInfo('America/Chicago')).isoformat(),
    )
