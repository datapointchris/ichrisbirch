# Documentation

Built with Material for MkDocs

Config file: `mkdocs.yml`
Directory: `docs/`
Docs build pipeline: `.github/workflows/deploy-docs.yml`

Docs are built using mkdocs automatically on push with the above pipeline, which triggers the `pages-build-deployment` Github workflow that publishes them to a `gh-pages` branch and publishes them to `datapointchris.github.io/ichrisbirch` from that branch.

Refer to [CICD](cicd.md) for a description of the pipeline.

## Github Settings

### Build and deployment

Source: Deploy from a branch

Branch: gh-pages / (root)

!!! note "Note"
    Even though this project is using Github Actions to publish the branch, the action is actually using `gh-deploy` so the source is NOT Github Actions, but rather "Deploy from a branch" that `gh-deploy` sets up.

    You might have to push the build once the first time to get the `gh-pages` branch to show up.
    This is the branch to use, not master, since part of the deploy script used `gh-deploy` which builds the `gh-pages` branch.

    In this branch, the root of the folder is the built docs, NOT /docs, because we are not building from the master branch where the docs live in /docs.

### Custom Domain

Custom domain: docs.ichrisbirch.com

!!! note "Note"
    CNAME record needs to be set up **before** adding the custom domain, or the lookup will fail.
