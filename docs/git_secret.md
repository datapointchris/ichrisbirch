# git-secret

[gpg cheatsheet](https://aws-labs.com/gpg-keys-cheatsheet/)

## Making a Secret

1. `git secret init` - for new repository
2. `git secret tell ichrisbirch@gmail.com`
   1. This user has to have a public GPG key on THIS computer
3. `git secret tell 'user@email.com'`
   1. Import this user's public GPG key
4. `git secret add .env`
5. `git secret hide`
6. Add and commit new .secret file(s)

## Getting a Secret

1. Git pull the .secret file(s)
2. `git secret reveal`

## Using git-secret with EC2 instance

### Make gpg key for EC2 instance

#### Local Machine

```bash
gpg --gen-key
# Real name: iChrisBirch EC2
# Email address: ec2@ichrisbirch.com

# Export and upload keys to EC2 Instance
gpg --export --armor "iChrisBirch EC2" > ec2-public.key
gpg --export-secret-key --armor "iChrisBirch EC2" > ec2-private.key
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

#### EC2 Instance

```bash
# Import keys
gpg --import ec2-public.key
gpg --import ec2-private.key

# Project Directory
git pull
git secret reveal
```

## Make a gpg key for CICD

```bash
# Generate new key, no passphrase
gpg --gen-key
# Export the secret key as one line, multiline not allowed
gpg --armor --export-secret-key datapointchris@github.com | tr '\n' ',' > cicd-gpg-key.gpg
# In the repository:
git secret reveal
git secret tell datapointchris@github.com
git secret hide
```

Add the key to the CICD environment secrets.
Add this to the CICD workflow, which will re-create the line breaks and import into gpg

```yaml
- name: "git-secret Reveal .env files"
  run: |
    # Import private key and avoid the "Inappropriate ioctl for device" error
    echo ${{ secrets.CICD_GPG_KEY }} | tr ',' '\n' | gpg --batch --yes --pinentry-mode loopback --import
    git secret reveal
```

!!! note "Note for Ubuntu 20.04"
    It is necessary to downgrade the version of gpg in MacOS to be compatible with the version running on Ubuntu 20.04, specifically the runners on GitHub Actions.
    <https://github.com/sobolevn/git-secret/issues/760#issuecomment-1126163319>

```bash
    brew uninstall git-secret
    brew uninstall gpg
    brew cleanup
    brew install gnupg@2.2
    # MUST add /usr/local/opt/gnupg@2.2/bin to PATH in dotfiles
    brew install git-secret
    # brew says it installs gnupg with git-secret, but after gpg still points to 2.2
    git secret clean
    git secret hide
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

# Set new expiry date for key and subkey(s)
gpg --quick-set-expire B98C7D8073BB87... 1y 2E418AB946A0ECA...

# Check that the keys are no longer expired
gpg --list-secret-keys --verbose --with-subkey-fingerprints

>>> sec   ed25519 2022-04-19 [SC] [expires: 2025-04-19]
>>>       B98C7D8073BB87...
>>> uid           [ultimate] Chris Birch <ichrisbirch@gmail.com>
>>> ssb   cv25519 2022-04-19 [E] [expires: 2025-04-19]
>>>       2E418AB946A0ECA...

# Remove the expired email address from `git-secret`
git secret removeperson ichrisbirch@gmail.com

>>> git-secret: removed keys.
>>> git-secret: now [ichrisbirch@gmail.com] do not have an access to the repository.
>>> git-secret: make sure to hide the existing secrets again.

# Hide the keys without the email (this may not be necessary)
git secret hide

>>> git-secret: done. 3 of 3 files are hidden.

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
