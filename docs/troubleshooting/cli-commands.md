# CLI Command Troubleshooting

This guide covers common CLI issues and solutions, particularly focusing on the **elimination of confusing command duplication** in the iChrisBirch CLI.

## 🎯 Overview

The CLI underwent a **major simplification** to eliminate confusing command duplication where multiple commands performed the same operation. This guide helps users adapt to the new simplified interface.

## 🚨 Common CLI Issues

### 1. Command Not Found - traefik Commands

**Problem**: Trying to use removed `traefik-*` commands

**Error Messages**:

```bash
$ icb traefik start dev
Unknown command: traefik

$ icb traefik status dev
Unknown command: traefik
```

**Root Cause**: All `traefik-*` commands were **intentionally removed** to eliminate confusing duplication

**Attempted Solutions (That Failed)**:

- Looking for `traefik` command in help output (it's no longer there)
- Trying variations like `icb traefik-start dev` (doesn't exist)
- Assuming the CLI is broken (it's working correctly, just simplified)

**Resolution**: Use the simplified commands instead

```bash
# WRONG (removed commands)
icb traefik start dev     → Use: icb dev start
icb traefik stop dev      → Use: icb dev stop
icb traefik restart dev   → Use: icb dev restart
icb traefik status dev    → Use: icb dev status
icb traefik logs dev      → Use: icb dev logs
icb traefik health dev    → Use: icb dev health

# CORRECT (current commands)
icb dev start             # Starts dev with Traefik + HTTPS
icb dev stop              # Stops dev environment
icb dev restart           # Restarts dev environment
icb dev status            # Shows status + HTTPS URLs
icb dev logs              # Shows service logs
icb dev health            # Runs health checks
```

**Prevention**: Use `icb help` to see all available commands. The simplified interface only shows actual working commands.

### 2. Confusion About Which Command to Use

**Problem**: Users confused about whether to use `dev start` or old `traefik start dev`

**Root Cause**: Historical documentation or muscle memory from the old duplicated interface

**Resolution**: Always use the environment-first commands

```bash
# SIMPLE RULE: Environment first, then action
ichrisbirch <environment> <action>

# Examples:
icb dev start         # Development environment
icb testing start    # Testing environment
icb prod start       # Production environment
```

**Benefits of Simplified Interface**:

- ✅ **No confusion**: Only one command per operation
- ✅ **Consistent patterns**: Same structure across all environments
- ✅ **Hidden complexity**: Users don't need to know about Traefik implementation
- ✅ **Professional UX**: Follows industry-standard CLI design patterns

### 3. SSL Manager Command Location

**Problem**: Looking for SSL commands under `traefik` namespace

**Error Messages**:

```bash
$ icb traefik ssl-manager generate dev
Unknown command: traefik
```

**Root Cause**: SSL manager is now a **top-level command**, not under `traefik`

**Resolution**: Use ssl-manager as a top-level command

```bash
# WRONG (old location)
icb traefik ssl-manager generate dev

# CORRECT (current location)
icb ssl-manager generate dev
icb ssl-manager info dev
icb ssl-manager validate dev
```

**Why This Changed**: SSL management is a fundamental operation that applies to all environments, not just Traefik-specific functionality.

### 4. Documentation References to Old Commands

**Problem**: Following outdated documentation that references `traefik-*` commands

**Root Cause**: Documentation that wasn't updated after CLI simplification

**Resolution**: Use the command translation guide

| Old Command (Removed) | New Command (Current) | Description |
| --- | --- | --- |
| `icb traefik start <env>` | `ichrisbirch <env> start` | Start environment |
| `icb traefik stop <env>` | `ichrisbirch <env> stop` | Stop environment |
| `icb traefik restart <env>` | `ichrisbirch <env> restart` | Restart environment |
| `icb traefik status <env>` | `ichrisbirch <env> status` | Environment status |
| `icb traefik logs <env>` | `ichrisbirch <env> logs` | View logs |
| `icb traefik health <env>` | `ichrisbirch <env> health` | Health checks |
| `icb traefik ssl-manager <cmd>` | `icb ssl-manager <cmd>` | SSL management |

**Prevention**: Always refer to the current [CLI Management Guide](../cli-traefik-usage.md) for up-to-date command references.

### 5. Help Command Not Showing Expected Options

**Problem**: Looking for `traefik` in help output

```bash
$ icb help
# traefik commands not listed
```

**Root Cause**: This is **correct behavior** - simplified CLI only shows available commands

**Resolution**: The help output is correct. Use environment-specific help

```bash
# General help (shows all top-level commands)
icb help

# Environment-specific help
icb dev help

# SSL manager help
icb ssl-manager help
```

**Expected Help Output**:

```bash
Available commands:
  dev start/stop/restart/status/logs/health    # Development environment
  testing start/stop/restart/status/logs/health # Testing environment
  prod start/stop/restart/status/logs/health    # Production environment
  ssl-manager generate/info/validate            # SSL certificate management
```

### 6. Script or Automation Using Old Commands

**Problem**: Automated scripts failing due to removed commands

**Error Messages**:

```bash
./deploy.sh: line 15: icb traefik start dev: command failed
```

**Root Cause**: Scripts written for the old duplicated CLI interface

**Resolution**: Update scripts to use simplified commands

```bash
# WRONG (will fail)
#!/bin/bash
icb traefik start dev
icb traefik health dev

# CORRECT (current)
#!/bin/bash
icb dev start
icb dev health
```

**Prevention**: Update all automation scripts and CI/CD pipelines to use the new simplified interface.

## 🔧 Advanced CLI Debugging

### Check CLI Installation

```bash
# Verify CLI is executable
ls -la ./cli/icb

# Make executable if needed
chmod +x ./cli/icb

# Test basic functionality
./cli/icb help
```

### Verify Current CLI Version

```bash
# Check CLI script for version information
head -20 ./cli/icb

# Look for the function definitions to confirm simplified interface
grep -n "function.*start\|function.*traefik" ./cli/icb
```

### Debug Command Parsing

```bash
# Enable bash debugging to see command parsing
bash -x ./cli/icb dev start

# Check if commands are being recognized
./cli/icb dev help
```

## 🚀 CLI Migration Guide

### For Individual Users

1. **Update muscle memory**: Practice using `<env> <action>` pattern
2. **Update bookmarks**: Replace any documented commands with new syntax
3. **Check scripts**: Update any personal scripts or aliases
4. **Use help commands**: Rely on `icb help` for current command reference

### For Teams

1. **Team training**: Ensure all developers know about the simplified interface
2. **Update documentation**: Review and update any team-specific documentation
3. **Update CI/CD**: Modify deployment scripts and automation
4. **Code review**: Check for old command usage in new scripts

### For Documentation

1. **Search and replace**: Find all references to `traefik-*` commands
2. **Update examples**: Replace with simplified command syntax
3. **Add migration notes**: Include transition guidance for users
4. **Test all examples**: Verify all documented commands actually work

## 🌟 Benefits of CLI Simplification

### User Experience Improvements

**Before (Confusing Duplication)**:

```bash
# Users had to choose between equivalent commands
icb traefik start dev    # Started dev environment
icb dev start            # Also started dev environment (same result)

# Problems:
# - Confusion about which command to use
# - Implementation details exposed (Traefik)
# - Inconsistent command patterns
# - More commands to remember
```

**After (Clean & Professional)**:

```bash
# One command per operation
icb dev start            # Clear, simple, consistent

# Benefits:
# - No confusion about which command to use
# - Implementation details hidden
# - Consistent patterns across all environments
# - Fewer commands to remember
```

### Technical Benefits

1. **Reduced Cognitive Load**: Fewer commands to learn and remember
2. **Better Discoverability**: `help` command shows only working commands
3. **Consistent Patterns**: Same structure for all environments
4. **Professional CLI Design**: Follows industry-standard CLI conventions
5. **Easier Maintenance**: Fewer code paths to maintain and test

### Development Workflow Benefits

1. **Faster Onboarding**: New developers learn one simple pattern
2. **Reduced Errors**: Fewer command options reduce user mistakes
3. **Better Documentation**: Clearer examples without command duplication
4. **Improved Scripts**: Simpler automation with consistent command patterns

## 🛠️ Command Reference Quick Card

### Current Simplified Commands

```bash
# Development
icb dev start|stop|restart|rebuild  # Manage dev environment
icb dev status|health               # Check environment
icb dev logs [service]              # View logs
icb dev smoke                       # Run smoke tests
icb dev is-ready                    # Quick health check (exit 0/1)
icb dev ensure                      # Start if not running
icb dev docker [service]            # Show merged compose config
icb dev db backup|restore|list|seed|init  # Database commands

# Testing
icb testing start|stop|restart|rebuild  # Manage test environment
icb testing status|health               # Check environment
icb testing logs [service]              # View logs
icb testing db backup|restore|list|seed|reset  # Database commands
icb test run [path] [args]              # Run pytest

# Production (blue/green aware)
icb prod start|stop|restart         # Manage production
icb prod status|health|apihealth    # Check environment
icb prod logs [service|deploy|build]  # View logs
icb prod smoke                      # Run smoke tests (requires ICHRISBIRCH_API_KEY)
icb prod deploy-status              # Show blue/green state
icb prod rollback                   # Switch traffic to previous color
icb prod build-test                 # Test production Docker build locally
icb prod db backup|restore|list|init  # Database commands

# Tools
icb ssl-manager generate|validate|info [env]  # SSL certificates
icb routing generate                # Regenerate Traefik routing
icb install                         # Symlink CLI to ~/.local/bin/icb
icb stats summary|code|tests|quality|activity|events|trends|churn  # Stats

# Help
icb help                # General help
icb dev help            # Development help
icb test help           # Test help
icb stats               # Stats submenu
```

### Removed Commands (Do Not Use)

```bash
# THESE COMMANDS NO LONGER EXIST:
icb traefik start <env>     # REMOVED
icb traefik stop <env>      # REMOVED
icb traefik restart <env>   # REMOVED
icb traefik status <env>    # REMOVED
icb traefik logs <env>      # REMOVED
icb traefik health <env>    # REMOVED
```

The CLI simplification provides a clean, professional interface that eliminates confusion and follows modern CLI design principles. The new simplified commands are more intuitive, easier to remember, and provide a better developer experience.
