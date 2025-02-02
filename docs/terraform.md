# Terraform

## Troubleshooting

### Terraform State is Locked

Github Runners sometimes lock the state.

Locally:
`terraform plan` -> This will give you an ID of the lock.
`terraform force-unlock $LOCK_ID`

### terraform plan -> backend configuration changed

Reference:
[Confusing error message when terraform backend is changed - Terraform - HashiCorp Discuss](https://discuss.hashicorp.com/t/confusing-error-message-when-terraform-backend-is-changed/32637)

```shell
➜ terraform plan
╷
│ Error: Backend initialization required: please run "terraform init"
│
│ Reason: Backend configuration block has changed
│
│ The "backend" is the interface that Terraform uses to store state,
│ perform operations, etc. If this message is showing up, it means that the
│ Terraform configuration you're using is using a custom configuration for
│ the Terraform backend.
│
│ Changes to backend configurations require reinitialization. This allows
│ Terraform to set up the new configuration, copy existing state, etc. Please run
│ "terraform init" with either the "-reconfigure" or "-migrate-state" flags to
│ use the current configuration.
│
│ If the change reason above is incorrect, please verify your configuration
│ hasn't changed and try again. At this point, no changes to your existing
│ configuration or state have been made.
╵


➜ terraform init
Initializing the backend...
╷
│ Error: Backend configuration changed
│
│ A change in the backend configuration has been detected, which may require migrating existing state.
│
│ If you wish to attempt automatic migration of the state, use "terraform init -migrate-state".
│ If you wish to store the current configuration with no changes to the state, use "terraform init -reconfigure".


➜ terraform init -migrate-state
Initializing the backend...
Backend configuration changed!

Terraform has detected that the configuration specified for the backend
has changed. Terraform will now check for existing state in the backends.

╷
│ Error: Failed to decode current backend config
│
│ The backend configuration created by the most recent run of "terraform init" could not be decoded: unsupported attribute "assume_role_duration_seconds". The configuration may have been initialized by an earlier version that
│ used an incompatible configuration structure. Run "terraform init -reconfigure" to force re-initialization of the backend.
╵


➜ terraform init -reconfigure
Initializing the backend...

Successfully configured the backend "s3"! Terraform will automatically
use this backend unless the backend configuration changes.
Initializing provider plugins...
- Reusing previous version of hashicorp/aws from the dependency lock file
- Reusing previous version of hashicorp/tls from the dependency lock file
- Using previously-installed hashicorp/aws v5.67.0
- Using previously-installed hashicorp/tls v4.0.6

Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that are required for your infrastructure. All Terraform commands
should now work.

If you ever set or change modules or backend configuration for Terraform,
rerun this command to reinitialize your working directory. If you forget, other
commands will detect it and remind you to do so if necessary.

```

This was caused by an upgrade to terraform, a new version had different configuration options.
