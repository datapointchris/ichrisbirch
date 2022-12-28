from flask import Blueprint, render_template
from datetime import datetime
from zoneinfo import ZoneInfo

from euphoria import __version__
from euphoria.backend.common import config

blueprint = Blueprint(
    'health',
    __name__,
    template_folder='templates/health',
    static_folder='static',
)


@blueprint.route('/')
def health():
    return render_template(
        'health/index.html',
        config=config,
        version=__version__,
        server_time=datetime.now().isoformat(),
        local_time=datetime.now(tz=ZoneInfo('America/Chicago')).isoformat(),
    )
