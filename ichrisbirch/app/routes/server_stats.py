from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Blueprint, render_template

from ichrisbirch.config import get_settings

settings = get_settings()

blueprint = Blueprint(
    'server_stats',
    __name__,
    template_folder='templates/server_stats',
    static_folder='static',
)


@blueprint.route('/')
def index():
    return render_template(
        'server_stats/index.html',
        settings=settings,
        server_time=datetime.now().isoformat(),
        local_time=datetime.now(tz=ZoneInfo('America/Chicago')).isoformat(),
    )
