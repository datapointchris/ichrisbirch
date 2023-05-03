# CICD

## `deploy-docs.yml`

Description:

Build the docs with mkdocs and run gh-deploy to publish them to github pages with the `pages-build-deployment` workflow.

## `python-cicd.yml`

Description:

### Key for Github Actions to Access EC2 Instance

`ICHRISBIRCH_KEY`

To generate this value locally:
`cat ichrisbirch-webserver.pem | pbcopy`
Simply paste into the secret on Github
