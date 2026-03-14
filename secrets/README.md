# secrets

Encrypted environment files managed by [SOPS](https://github.com/getsops/sops) + [age](https://github.com/FiloSottile/age).

## Prerequisites

- `sops` and `age` installed
- age private key at `~/.config/sops/age/keys.txt`

## Edit production secrets

```bash
sops secrets/secrets.prod.enc.env
```

Opens in `$EDITOR`. SOPS decrypts on open, re-encrypts on save.

## Decrypt to stdout

```bash
sops decrypt secrets/secrets.prod.enc.env
```

## Add a new secret

```bash
sops secrets/secrets.prod.enc.env
# Add NEW_VAR=value, save
```

## Key distribution

Copy `~/.config/sops/age/keys.txt` to any machine that needs to decrypt.
The public key in `.sops.yaml` is safe to share.
