# Terraform

## Troubleshooting

### Terraform State is Locked

Github Runners sometimes lock the state.

Locally:
`terraform plan` -> This will give you an ID of the lock.
`terraform force-unlock $LOCK_ID`
