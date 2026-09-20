# Setup a New Server

Production runs in a Proxmox LXC container with Docker and a Cloudflare Tunnel.
`scripts/bootstrap-homelab.sh` stands one up.

```bash
# as root on the container
curl -fsSL https://raw.githubusercontent.com/datapointchris/ichrisbirch/main/scripts/bootstrap-homelab.sh | bash
```

[Homelab Production Deployment](../homelab-deployment.md) covers the LXC
settings the container needs, the tunnel configuration, and the manual
equivalent of each step the script takes.

## What the script needs from you

Three things cannot come from the container itself, and the script prompts for
each: AWS credentials, the age private key, and a Cloudflare tunnel token.

**AWS credentials.** Used for S3 database backups and nothing else. Either run
`aws configure` when prompted or copy `~/.aws` from another machine.
`aws sts get-caller-identity` confirms it afterwards.

**The age private key.** Production secrets are SOPS-encrypted at
`secrets/secrets.prod.enc.env`, and the host cannot decrypt its own `.env`
without this key:

```bash
scp ~/.config/sops/age/keys.txt <host>:~/.config/sops/age/keys.txt
```

**A Cloudflare tunnel token.** Create the tunnel in the Cloudflare dashboard
under Zero Trust, Networks, Tunnels, then hand the script its token. The tunnel
is what terminates TLS and reaches the container, so nothing on the host listens
on a public port.

## Database

The script offers three paths: migrate a fresh database, restore from a dump
file, or skip because the database is already set up.

A restore runs `pg_restore` against the infrastructure Postgres:

```bash
docker exec -i icb-infra-postgres \
  pg_restore -U icb_app -d ichrisbirch --no-owner < <dump-file>
```

## Afterwards

```bash
icbops prod deploy-status
icbops prod health
icbops prod smoke
```

Deploys then happen by pushing to `main`. The webhook host receives the push
and runs the blue/green deploy. See [Blue/Green
Deployment](../blue-green-deployment.md).

## Related

- [Homelab Production Deployment](../homelab-deployment.md)
- [Blue/Green Deployment](../blue-green-deployment.md)
- [NGINX](nginx.md) and [Supervisor](supervisor.md), which the bare-metal
  deployment used
