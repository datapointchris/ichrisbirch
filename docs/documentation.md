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

Refer to [Domain Names](domain_names.md) for setting up the subdomain.

!!! note "Note"
    CNAME record needs to be set up **before** adding the custom domain, or the lookup will fail.
    CNAME record goes in the `/docs` folder because that folder is built as the root on the `gh-pages` branch that is set up with that file when hosting.

### Diagrams

[Online FlowChart & Diagrams Editor - Mermaid Live Editor](https://mermaid.live/edit)

[GitHub - mingrammer/diagrams: Diagram as Code for prototyping cloud system architectures](https://github.com/mingrammer/diagrams)

### TODO: Read these things

[Vale.sh - A linter for prose](https://vale.sh)

[Python's doctest: Document and Test Your Code at Once – Real Python](https://realpython.com/python-doctest/)

Awesome documentation example for small project:
[Documentation — pypdf 3.5.1 documentation](https://pypdf.readthedocs.io/en/stable/dev/documentation.html)

[A Guide to Writing Your First Software Documentation — SitePointSitePoint](https://www.sitepoint.com/writing-software-documentation/)

[How to Write Documentation For Your Next Software Development Project](https://www.freecodecamp.org/news/how-to-write-documentation-for-your-next-software-development-project/)

[Software Documentation Best Practices [With Examples] helpjuice-logo-0307896d1acd18c6a7f52c4256467fb6ca1007315c373af21357496e9ceb49e2](<https://helpjuice.com/blog/software-documentation>)

[Software Documentation Types and Best Practices | by AltexSoft Inc | Prototypr](https://blog.prototypr.io/software-documentation-types-and-best-practices-1726ca595c7f)

[Prepare the documentation for successful software project development](https://upplabs.com/blog/how-to-prepare-the-documentation-for-successful-software-project-development/)

[How to Write Technical Documentation With Empathy | by Edward Huang | Jan, 2023 | Better Programming](https://betterprogramming.pub/how-to-write-technical-documentation-with-empathy-f321104746f3)
