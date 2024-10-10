import json
import os
import smtplib
import subprocess
import sys
import tempfile
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

WEBSERVER_NAME = 'ichrisbirch_webserver'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_FROM = EMAIL_USERNAME = 'ichrisbirch@gmail.com'
EMAIL_TO = 'chrisbirch@live.com'
EMAIL_SUBJECT_PREFIX = 'iChrisBirch Infrastructure Changes - '
EMAIL_PASSWORD = os.getenv('GMAIL_APP_PASSWORD') or sys.argv[1]
TIMEOUT = 60  # Timeout in seconds (2 minutes)

if EMAIL_PASSWORD:
    print('GMAIL_APP_PASSWORD found in environment')


def infrastrucuture_has_changes(outfile: Path) -> bool:
    cmd = ['terraform', 'plan', '-detailed-exitcode', '-out', str(outfile), '-no-color']
    result = subprocess.run(cmd, capture_output=True, timeout=TIMEOUT)
    print()
    print('---------- Terraform Plan Result ----------')
    print(result.stdout.decode())
    print()
    print('Terraform Plan Exit Code:', result.returncode)
    return result.returncode == 2


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
    email_subject = EMAIL_SUBJECT_PREFIX
    print('Working Directory: ', subprocess.run('pwd', capture_output=True).stdout.decode())

    with tempfile.NamedTemporaryFile() as tf_outfile, tempfile.NamedTemporaryFile() as tf_jsonfile:
        outfile_path = Path(tf_outfile.name)
        jsonfile_path = Path(tf_jsonfile.name)

        print('Checking for infrastructure changes...')
        print()
        if infrastrucuture_has_changes(outfile_path):
            print('Infrastructure changes detected')
            generate_terraform_plan_json(outfile_path, jsonfile_path)
            print('Generated terraform plan JSON')
            plan_changes = parse_terraform_plan_changes(jsonfile_path)
            webserver_terminated = is_webserver_terminated(plan_changes)
            additional_changes = has_additional_changes(plan_changes)
            changes_text = subprocess.getoutput(f'terraform show -no-color {outfile_path}')

            if webserver_terminated and not additional_changes:
                print('Webserver terminated, re-creating...')
                apply_terraform_plan(outfile_path)
                email_subject += f'{WEBSERVER_NAME} Terminated'
                email_body = f"""<h2>{WEBSERVER_NAME} was terminated!!</h2>
                Re-created the webserver successfully.\n\n<pre>{changes_text}</pre>"""

            elif webserver_terminated and additional_changes:
                print('Webserver terminated, additional changes detected, pending review...')
                email_subject += f'{WEBSERVER_NAME} Terminated and Unexpected Infrastructure Changes Detected'
                email_body = f"""<h2>{WEBSERVER_NAME} was terminated!!</h2>
                Could not re-create the webserver, pending review of additional changes:\n\n<pre>{changes_text}</pre>"""

            elif not webserver_terminated and additional_changes:
                print('Unexpected infrastructure changes detected, pending review...')
                email_subject += 'Unexpected Infrastructure Changes Detected'
                email_body = f"""<h2>Unexpected infrastructure changes detected, pending review:</h2>
                    <pre>{changes_text}</pre>"""

            print(f'Sending email to {EMAIL_TO}')
            send_email(email_subject, email_body)
            print('Email sent successfully')
            exit(0)
        else:
            print('No infrastructure changes detected')
            exit(0)
