import json
import sys
import smtplib
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

WEBSERVER_NAME = 'ichrisbirch_webserver'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_FROM = EMAIL_USERNAME = 'ichrisbirch@gmail.com'
EMAIL_TO = 'chrisbirch@live.com'
EMAIL_SUBJECT_PREFIX = 'iChrisBirch Infrastructure Changes - '
EMAIL_PASSWORD = sys.argv[1]
TERRAFORM_PLAN_FILE = Path('tfplan')
TIMEOUT = 60


def generate_terraform_plan_json(outfile: Path, jsonfile: Path):
    cmd = ['terraform', 'show', '-json', str(outfile)]
    with jsonfile.open('w') as f:
        subprocess.run(cmd, stdout=f, timeout=TIMEOUT)


def parse_terraform_plan_changes(filename: Path) -> list:
    return list(json.load(filename.open()).get('resource_changes', []))


def is_webserver_terminated(changes: list) -> bool:
    for change in changes:
        if change['type'] == 'aws_instance' and change['name'] == WEBSERVER_NAME:
            if 'create' in change['change']['actions']:
                return True
    return False


def has_additional_changes(changes: list) -> bool:
    for change in changes:
        if change['change']['actions'] != ['no-op'] and change['name'] != WEBSERVER_NAME:
            return True
    return False


def apply_terraform_plan(outfile: Path):
    cmd = ['terraform', 'apply', '-auto-approve', str(outfile)]
    subprocess.run(cmd, timeout=TIMEOUT)


def send_email(subject: str, body: str):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg['X-Priority'] = '2'
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'html'))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())


if __name__ == '__main__':
    print('Working Directory: ', subprocess.run('pwd', capture_output=True).stdout.decode())
    
    jsonfile = Path('terraform_plan.json')
    generate_terraform_plan_json(TERRAFORM_PLAN_FILE, jsonfile)
    print(f'Generated terraform plan JSON from {TERRAFORM_PLAN_FILE}')
    
    plan_changes = parse_terraform_plan_changes(jsonfile)
    webserver_terminated = is_webserver_terminated(plan_changes)
    additional_changes = has_additional_changes(plan_changes)
    changes_text = subprocess.getoutput(f'terraform show -no-color {TERRAFORM_PLAN_FILE}')

    email_subject = EMAIL_SUBJECT_PREFIX
    email_body = 'TEST BODY'
    if webserver_terminated and not additional_changes:
        print('Webserver was terminated, re-creating...')
        apply_terraform_plan(TERRAFORM_PLAN_FILE)
        email_subject += f'{WEBSERVER_NAME} Terminated'
        email_body = f"""<h2>{WEBSERVER_NAME} was terminated!!</h2>
        Re-created the webserver successfully.\n\n<pre>{changes_text}</pre>"""

    elif webserver_terminated and additional_changes:
        print('Webserver was terminated, additional changes detected, pending review...')
        email_subject += f'{WEBSERVER_NAME} Terminated and Unexpected Infrastructure Changes Detected'
        email_body = f"""<h2>{WEBSERVER_NAME} was terminated!!</h2>
        Could not re-create the webserver, pending review of additional changes:\n\n<pre>{changes_text}</pre>"""

    elif not webserver_terminated and additional_changes:
        print('Unexpected infrastructure changes detected, pending review...')
        email_subject += 'Unexpected Infrastructure Changes Detected'
        email_body = f"""<h2>Unexpected infrastructure changes detected, pending review:</h2>
            <pre>{changes_text}</pre>"""

    print()
    print(f'Sending email to {EMAIL_TO}')
    send_email(email_subject, email_body)
    print('Email sent successfully')
