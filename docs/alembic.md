# Alembic Revision

Run in `ichrisbirch/ichrisbirch` (where `alembic.ini` is located)

1. Make the changes to the models and schemas

2. Run a revision to pickup changes in code
`alembic revision --autogenerate -m 'Add notes field to tasks table'`

    > **Note**  
    > If this doesn't work perfectly, you must edit the revision file

3. Run the upgrade in the environments

!!! note "Locally"
    ```bash
    export ENVIRONMENT='development'
    alembic upgrade head
    ```

!!! info "EC2"
    ```bash
    export ENVIRONMENT='production'
    alembic upgrade head
    ```

## Troubleshooting

!!! failure "Error"
    Alembic is not able to upgrade to the latest because the revisions got out of sync.

    !!! success "Solution"
        Find the last revision that was successfully run (manually by inspecting the database) and then run:
        `alembic stamp <revision>` to set the current revision to the last successful one.
        Then run the upgrade again:
        `alembic upgrade head`
