# Troubleshooting Guide

This comprehensive troubleshooting guide documents common issues, their root causes, attempted solutions, and final resolutions encountered during the development and operation of the iChrisBirch project.

## Overview

The troubleshooting documentation is organized by component and includes:

- **Problem description**: Clear statement of the issue
- **Root cause analysis**: Technical explanation of why the issue occurs
- **Attempted solutions**: What was tried and why it didn't work
- **Final resolution**: Working solution with implementation details
- **Prevention**: How to avoid the issue in the future

## Quick Reference

### Common Issues by Component

| Page                                   | Covers                               | First move                     |
| -------------------------------------- | ------------------------------------ | ------------------------------ |
| [Docker](docker-issues.md)             | Build failures, container networking | Check Dockerfile and networks  |
| [Testing](testing-issues.md)           | Stale containers, an empty test DB   | Work the escalation ladder     |
| [Database](database-issues.md)         | Connection errors, schema issues     | Check the connection string    |
| [Development](development-issues.md)   | Setup problems, tooling conflicts    | Follow the setup guide         |

### Start with the escalation ladder

Most dev and test failures are stale container state rather than bugs. Clearing
them costs less than reading logs:

```bash
./ops/icbops testing stop && ./ops/icbops testing start   # ~30s
./ops/icbops testing rebuild --volumes                    # ~60-90s
```

Only after both is a manual `docker` subcommand worth reaching for.
[A change is not taking effect](testing-issues.md#a-change-is-not-taking-effect)
covers what each step fixes.

After a failed test run, read `/tmp/ichrisbirch-pytest-output.log` and
`/tmp/ichrisbirch-pytest-report.json` rather than re-running the suite.

### Emergency fixes

For urgent production issues:

1. **Service down**: [deployment issues](deployment-issues.md#service-recovery)
2. **Database connection**: [database troubleshooting](database-issues.md#connection-issues)
3. **A deploy failed**: [what the pipeline logs](deployment-issues.md#a-deploy-failed)

## Also in This Guide

- [SSL Certificates](ssl-certificates.md) — browser trust warnings, mkcert, and the OpenSSL fallback
- [CLI Commands](cli-commands.md) — errors from the removed `traefik-*` commands and what replaced them
- [Deployment Issues](deployment-issues.md) — prod service recovery, failed builds, cert expiry, migration failures
- [API JWT Wrong Database](api-jwt-wrong-database.md) — empty; nothing has been written here yet

## How to Use This Guide

1. **Identify the component** where the issue is occurring
2. **Check the quick reference** for immediate solutions
3. **Read the detailed troubleshooting page** for comprehensive guidance
4. **Follow the resolution steps** with provided code examples
5. **Apply prevention measures** to avoid future occurrences

## Contributing

When you encounter and solve a new issue:

1. Document it in the appropriate section
2. Include error messages, logs, and code snippets
3. Explain the root cause and why the solution works
4. Add prevention tips for future reference

## Legacy Issues

Historical troubleshooting information has been migrated from the original troubleshooting.md file and integrated into the appropriate component-specific pages while maintaining all the original solutions and context.
