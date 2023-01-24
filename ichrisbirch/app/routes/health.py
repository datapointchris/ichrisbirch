from flask import Blueprint, render_template
from datetime import datetime
from zoneinfo import ZoneInfo

from ichrisbirch import __version__
from ichrisbirch import settings

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
        settings=settings,
        version=__version__,
        server_time=datetime.now().isoformat(),
        local_time=datetime.now(tz=ZoneInfo('America/Chicago')).isoformat(),
    )
