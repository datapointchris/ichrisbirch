---
id: uizgt2cn
title: troubleshooting
file_version: 1.1.3
app_version: 1.16.4
---

# Troubleshooting

## Flask

!!! failure "Error"<br/>
Blank pages loading, but no errors.

```
!!! success "Solution"
    Try a different port
    Sometimes the port is busy or used, but does not give a 'port in use' error
```

## Poetry

!!! failure "Error"<br/>
ModuleNotFoundError: No module named 'cachecontrol' when running poetry:

!!! success "Solution" `sudo apt install python3-cachecontrol`

## Supervisor

!!! failure "Error" supervisor.sock no such file

```
!!! success "Solution"
    make sure directories and files for logs are created.
```

!!! failure "Error"<br/>
BACKOFF can't find command... that is pointing to .venv

```
!!! success "Solution"
    Prod: Check that the project is installed
    Dev: Check the symlink isn't broken
```

!!! failure "Error"<br/>
`bash error: <class 'FileNotFoundError'>, [Errno 2] No such file or directory: file: /usr/local/Cellar/supervisor/4.2.5/libexec/lib/python3.11/site-packages/supervisor/xmlrpc.py line: 55`

```
!!! success "Solution"
    Start and run supervisor with homebrew: `brew services start supervisor`
```

!!! failure "Error" `log FileNotFoundError: [Errno 2] No such file or directory: '/var/www/ichrisbirch/ichrisbirch/NoneNone/pylogger.log'`

```
!!! success "Solution"
The environment file has not been loaded. **Most likely** you need to run `git secret reveal`
This happens when the project has been cloned for the first time or directory has been deleted or the env files might have changed.
```

## NGINX

!!! failure "Error"<br/>
bind() to 0.0.0.0:80 failed (98: Address already in use)

```
!!! success "Solution"
    `sudo pkill -f nginx & wait $!`
    `sudo systemctl start nginx`
```

!!! failure "Error" **DEV** bind() to 127.0.0.1:80 failed (13: Permission denied)

```
!!! success "Solution"
    NGINX is not running as root.  It does not run reliably with homebrew.
    Use `sudo nginx -s reload` instead of homebrew.
```

## API Postgres

!!! failure "Error"<br/>
\[error\] 94580#0: \*18 kevent() reported that connect() failed (61: Connection refused) while connecting to upstream, client: 127.0.0.1, server: api.localhost, request: "GET / HTTP/1.1", upstream: "[http://127.0.0.1:4200/](http://127.0.0.1:4200/)", host: "api.macmini.local

!!! success "Solution" DB cannot connect. Postgres string was built wrong, corrected by adding a test to check config is loaded properly.

!!! failure "Error"<br/>
Local changes were working but nothing that connected to prod postgres.

```
`api.ichrisbirch.com/tasks/` - 502 Bad Gateway
`api.ichrisbirch.com` Success redirect to `/docs`
`ichrisbirch.com` redirects to www in browser but error with requests
`www.ichrisbirch.com/tasks/` - Internal Server Error
Can connect to prod server with DBeaver
Verified that the connection info is the same.
Seems that the API is not connecting to postgres instance

**api.macmini.local**
WORKING api.macmini.local/
WORKING api.macmini.local/docs
WORKING api.macmini.local/tasks
WORKING api.macmini.local/tasks/1
WORKING api.macmini.local/tasks/completed

**ichrisbirch.com**
WORKING api.ichrisbirch.com/
WORKING api.ichrisbirch.com/docs
ERROR api.ichrisbirch.com/tasks
ERROR api.ichrisbirch.com/tasks/1
ERROR api.ichrisbirch.com/tasks/completed

!!! success "Solution"
    The issue was resolved by modifying the security group of the postgres instance to allow the ec2 instance to connect by allowing it's security group.
```

## Pytest

!!! failure "Error" E assert 307 == 200 E + where 307 = <Response \[307\]>.status\_code

```
!!! success "Solution"
    The trailing `/` is missing from the endpoint being called in the test, resulting in a 307 Temporary Redirect
    To fix:
    `/endpoint` --> `/endpoint/`
```

## Alembic

!!! failure "Error" Alembic is not able to upgrade to the latest because the revisions got out of sync.

```
!!! success "Solution"
    Find the last revision that was successfully run (manually by inspecting the database) and then run:
    `alembic stamp <revision>` to set the current revision to the last successful one.
    Then run the upgrade again:
    `alembic upgrade head`
```

<br/>

This file was generated by Swimm. [Click here to view it in the app](https://app.swimm.io/repos/Z2l0aHViJTNBJTNBaWNocmlzYmlyY2glM0ElM0FkYXRhcG9pbnRjaHJpcw==/docs/uizgt2cn).
