# Troubleshooting

## 🔧 Infrastructure & Deployment

### CLI Commands

- **[CLI Command Troubleshooting](troubleshooting/cli-commands.md)** - Issues with simplified CLI interface and eliminated command duplication

### SSL Certificates

- **[SSL Certificate Troubleshooting](troubleshooting/ssl-certificates.md)** - Browser warnings, mkcert setup, and certificate validation issues

## 🚨 Application Issues

## Configuration

!!! failure "Error"
    ```log
    FileNotFoundError: [Errno 2] No such file or directory: '/var/www/ichrisbirch/ichrisbirch/NoneNone/pylogger.log'
    ```

!!! success "Solution"
    The `.env` file is missing. For development, copy `.env.example` to `.env` and fill in values.
    For production, decrypt secrets: `sops decrypt secrets/secrets.prod.enc.env > .env`

## Pytest

!!! failure "Error"
    E       assert 307 == 200
    E        +  where 307 = <Response [307]\>.status_code

!!! success "Solution"
    The trailing `/` is missing from the endpoint being called in the test, resulting in a 307 Temporary Redirect
    To fix:
    `/endpoint` --> `/endpoint/`

## Alembic

!!! failure "Error"
    Alembic is not able to upgrade to the latest because the revisions got out of sync.

!!! success "Solution"
    Find the last revision that was successfully run (manually by inspecting the database) and then run:
    `alembic stamp <revision>` to set the current revision to the last successful one.
    Then run the upgrade again:
    `alembic upgrade head`

## FastAPI

!!! failure "Error"
     Request Error: Client error '405 Method Not Allowed' for url xxx

!!! success "Solution"
    Make sure that the `id` is being passed correctly for routes like `/endpoint/{id}/`
    The error will not say `id` is not found, it will give a 405 error because the url is not correct

---

!!! failure "Error"
    `PATCH` endpoint giving: 422 Unprocessable Entity: {"detail":[{"type":"missing","loc":["body","id"],"msg":"Field required"

!!! success "Solution"
    `PATCH` endpoints require the ID in the endpoint, but *also* the ID must be passed in the payload for the model so it can update the record in the DB by ID.
