from flask import Blueprint, render_template, url_for


blueprint = Blueprint(
    'app1',
    __name__,
    template_folder='templates/app1',
    static_folder='static',
)


@blueprint.route('/')
def index():
    return render_template('app1/index.html')


@blueprint.route('/page1')
def page1():
    return render_template('app1/page1.html')


@blueprint.route('/page2')
def page2():
    return render_template('app1/page2.html')
