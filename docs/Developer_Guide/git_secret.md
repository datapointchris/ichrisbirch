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
scp -i ~/.ssh/apps.pem ec2-public.key ubuntu@ichrisbirch:~
scp -i ~/.ssh/apps.pem ec2-private.key ubuntu@ichrisbirch:~

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

SUCCESS!!!
