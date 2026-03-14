# Developer Setup

## Prerequisites

- Docker Desktop
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [mkcert](https://github.com/FiloSottile/mkcert) (for local HTTPS certificates)

## Setup

```bash
git clone https://github.com/datapointchris/ichrisbirch.git
cd ichrisbirch/

# Install dependencies
uv sync

# Copy and fill in environment variables
cp .env.example .env
# Edit .env with your values

# Install pre-commit hooks
pre-commit install

# Generate SSL certificates for local development
./cli/ichrisbirch ssl-manager generate dev

# Start development environment
./cli/ichrisbirch dev start
```

## Access

- App: <https://app.docker.localhost/>
- API: <https://api.docker.localhost/>
- Chat: <https://chat.docker.localhost/>

## Secrets management

Production secrets are managed with SOPS + age. See `secrets/README.md` for details.

To edit production secrets:

```bash
# Requires age private key at ~/.config/sops/age/keys.txt
sops secrets/secrets.prod.enc.env
```
