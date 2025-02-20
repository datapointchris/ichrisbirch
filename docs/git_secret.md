# git-secret

!!! danger
    It seems that if `gpg` is updated then it causes some or all of the keys to need to be re-imported with `git secret`  
    Also if there is a mismatch between `gpg` versions between computers or cicd and macos then it can create an issue.  
    Overall, this is not the best way of handling secrets :sadface:

## Making a Secret

```shell
# for new repository
git secret init

# This user has to have a public GPG key on THIS computer
git secret tell ichrisbirch@gmail.com

git secret add .env
git secret hide

git commit -am 'build: add secret .env file'
```

## Using git-secret with EC2 instance

### Make gpg key for EC2 instance on local machine

```bash
gpg --gen-key
# Real name: iChrisBirch EC2
# Email address: ec2@ichrisbirch.com

# Export and upload keys to EC2 Instance
gpg --export --armor ec2@ichrisbirch.com > ec2-public.key
gpg --export-secret-key --armor ec2@ichrisbirch.com > ec2-private.key
scp -i ~/.ssh/ichrisbirch-webserver.pem ec2-public.key ubuntu@ichrisbirch:~
scp -i ~/.ssh/ichrisbirch-webserver.pem ec2-private.key ubuntu@ichrisbirch:~

# Project Directory
git secret tell ec2@ichrisbirch.com
# to re-encrypt them with the new authorized user
git secret reveal
git secret hide
git add .
git commit -m 'ops: Update secrets with new authorized user'
git push
```

### Import gpg key on EC2 Instance

```bash
# Import keys
gpg --import ec2-public.key
gpg --import ec2-private.key

# Project Directory
git pull
git secret reveal
```

## Make a gpg key for CICD

### Make a new key locally

```bash
# Generate new key, no passphrase
gpg --gen-key
# Export the secret key as one line, multiline not allowed
gpg --armor --export-secret-key datapointchris@github.com | tr '\n' ',' > cicd-gpg-key.gpg
# In the repository, make sure to add the new identity to allowed:
git secret tell datapointchris@github.com
git secret hide
```

### Add the key to the CICD environment secrets

### Add Run Step to CICD workflow

```yaml
- name: "git-secret Reveal .env files"
  run: |
    # Import private key and avoid the "Inappropriate ioctl for device" error
    echo ${{ secrets.CICD_GPG_KEY }} | tr ',' '\n' | gpg --batch --yes --pinentry-mode loopback --import
    git secret reveal
```

## Expired GPG key

**`git-secret: warning: at least one key for email(s) is revoked, expired, or otherwise invalid: ichrisbirch@gmail.com`**

Expired keys need to have their expiry date extended, which requires the following steps:

```bash
# List keys and subkey(s)
gpg --list-secret-keys --verbose --with-subkey-fingerprints

>>> sec   ed25519 2022-04-19 [SC] [expired: 2024-04-18]
>>>       B98C7D8073BB87...
>>> uid           [ultimate] Chris Birch <ichrisbirch@gmail.com>
>>> ssb   cv25519 2022-04-19 [E] [expired: 2024-04-18]
>>>       2E418AB946A0ECA...

# Set new expiry date for primary key and subkey(s)
# NOTE: MUST put the primary key first, expire date, subkeys after in the same command
gpg --quick-set-expire B98C7D8073BB87... 1y 2E418AB946A0ECA...

# Check that the keys are no longer expired
gpg --list-secret-keys --verbose --with-subkey-fingerprints

>>> sec   ed25519 2022-04-19 [SC] [expires: 2025-04-19]
>>>       B98C7D8073BB87...
>>> uid           [ultimate] Chris Birch <ichrisbirch@gmail.com>
>>> ssb   cv25519 2022-04-19 [E] [expires: 2025-04-19]
>>>       2E418AB946A0ECA...

# Remove the expired email address for git-secret
git secret removeperson ichrisbirch@gmail.com

>>> git-secret: removed keys.
>>> git-secret: now [ichrisbirch@gmail.com] do not have an access to the repository.
>>> git-secret: make sure to hide the existing secrets again.

# Add the email address as authorized viewer
git secret tell ichrisbirch@gmail.com

git-secret: done. ichrisbirch@gmail.com added as user(s) who know the secret.

# Hide the secrets again
git secret hide

>>> git-secret: done. 3 of 3 files are hidden.

# Check status to see that they are hidden
git status

>>>        modified:   .dev.env.secret
>>>        modified:   .gitsecret/keys/pubring.kbx
>>>        modified:   .gitsecret/keys/pubring.kbx~
>>>        modified:   .prod.env.secret
>>>        modified:   .test.env.secret
```
