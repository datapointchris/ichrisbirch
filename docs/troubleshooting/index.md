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

| Component | Common Issues | Quick Solutions |
|-----------|---------------|-----------------|
| [Docker](docker-issues.md) | Build failures, container networking | Check Dockerfile syntax, network configuration |
| [Poetry to UV Migration](poetry-uv-migration.md) | Dependency management, virtual environments | Follow migration checklist |
| [Testing](testing-issues.md) | Test failures, pytest not found, Docker issues | Verify test dependencies, rebuild images |
| [Database](database-issues.md) | Connection errors, schema issues | Check connection strings, run migrations |
| [Development Environment](development-issues.md) | Setup problems, tooling conflicts | Follow setup guide step-by-step |

### Recent Critical Issues (July 2025)

**Docker Network Conflicts During Testing:**

- **Issue**: Test runs fail with "failed to set up container networking: network not found" errors
- **Resolution**: Implemented comprehensive cleanup function with pre/post cleanup and multiple fallback strategies
- **Details**: [Docker Network Conflicts](testing-issues.md#docker-network-conflicts-during-testing)

**Testing Infrastructure Failures:**

- `error: Failed to spawn: 'pytest'` → Missing `--group test` in Dockerfile
- `service has neither an image nor a build context` → Add build directive to compose services  
- `ModuleNotFoundError: tests.utils.environment` → Fix import paths in conftest.py
- Docker network conflicts → Run comprehensive Docker cleanup

See [Testing Issues - Recent Critical Issues](testing-issues.md#recent-critical-issues-july-2025) for detailed solutions.

### Emergency Fixes

For urgent production issues:

1. **Service Down**: Check [deployment issues](deployment-issues.md#service-recovery)
2. **Database Connection**: See [database troubleshooting](database-issues.md#connection-issues)
3. **Test Failures**: Review [testing diagnostics](testing-issues.md#test-failure-diagnosis)

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
