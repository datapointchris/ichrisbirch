# CLI Command Troubleshooting

This guide covers common CLI issues and solutions, particularly focusing on the **elimination of confusing command duplication** in the iChrisBirch CLI.

## 🎯 Overview

The CLI underwent a **major simplification** to eliminate confusing command duplication where multiple commands performed the same operation. This guide helps users adapt to the new simplified interface.

## 🚨 Common CLI Issues

### 1. Command Not Found - traefik Commands

**Problem**: Trying to use removed `traefik-*` commands

**Error Messages**:

```bash
$ ichrisbirch traefik start dev
Unknown command: traefik

$ ichrisbirch traefik status dev  
Unknown command: traefik
```

**Root Cause**: All `traefik-*` commands were **intentionally removed** to eliminate confusing duplication

**Attempted Solutions (That Failed)**:

- Looking for `traefik` command in help output (it's no longer there)
- Trying variations like `ichrisbirch traefik-start dev` (doesn't exist)
- Assuming the CLI is broken (it's working correctly, just simplified)

**Resolution**: Use the simplified commands instead

```bash
# WRONG (removed commands)
ichrisbirch traefik start dev     → Use: ichrisbirch dev start
ichrisbirch traefik stop dev      → Use: ichrisbirch dev stop
ichrisbirch traefik restart dev   → Use: ichrisbirch dev restart
ichrisbirch traefik status dev    → Use: ichrisbirch dev status
ichrisbirch traefik logs dev      → Use: ichrisbirch dev logs
ichrisbirch traefik health dev    → Use: ichrisbirch dev health

# CORRECT (current commands)
ichrisbirch dev start             # Starts dev with Traefik + HTTPS
ichrisbirch dev stop              # Stops dev environment  
ichrisbirch dev restart           # Restarts dev environment
ichrisbirch dev status            # Shows status + HTTPS URLs
ichrisbirch dev logs              # Shows service logs
ichrisbirch dev health            # Runs health checks
```

**Prevention**: Use `ichrisbirch help` to see all available commands. The simplified interface only shows actual working commands.

### 2. Confusion About Which Command to Use

**Problem**: Users confused about whether to use `dev start` or old `traefik start dev`

**Root Cause**: Historical documentation or muscle memory from the old duplicated interface

**Resolution**: Always use the environment-first commands

```bash
# SIMPLE RULE: Environment first, then action
ichrisbirch <environment> <action>

# Examples:
ichrisbirch dev start         # Development environment
ichrisbirch testing start    # Testing environment  
ichrisbirch prod start       # Production environment
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
$ ichrisbirch traefik ssl-manager generate dev
Unknown command: traefik
```

**Root Cause**: SSL manager is now a **top-level command**, not under `traefik`

**Resolution**: Use ssl-manager as a top-level command

```bash
# WRONG (old location)
ichrisbirch traefik ssl-manager generate dev

# CORRECT (current location)
ichrisbirch ssl-manager generate dev
ichrisbirch ssl-manager info dev
ichrisbirch ssl-manager validate dev
```

**Why This Changed**: SSL management is a fundamental operation that applies to all environments, not just Traefik-specific functionality.

### 4. Documentation References to Old Commands

**Problem**: Following outdated documentation that references `traefik-*` commands

**Root Cause**: Documentation that wasn't updated after CLI simplification

**Resolution**: Use the command translation guide

| Old Command (Removed) | New Command (Current) | Description |
|----------------------|----------------------|-------------|
| `ichrisbirch traefik start <env>` | `ichrisbirch <env> start` | Start environment |
| `ichrisbirch traefik stop <env>` | `ichrisbirch <env> stop` | Stop environment |
| `ichrisbirch traefik restart <env>` | `ichrisbirch <env> restart` | Restart environment |
| `ichrisbirch traefik status <env>` | `ichrisbirch <env> status` | Environment status |
| `ichrisbirch traefik logs <env>` | `ichrisbirch <env> logs` | View logs |
| `ichrisbirch traefik health <env>` | `ichrisbirch <env> health` | Health checks |
| `ichrisbirch traefik ssl-manager <cmd>` | `ichrisbirch ssl-manager <cmd>` | SSL management |

**Prevention**: Always refer to the current [CLI Management Guide](../cli-traefik-usage.md) for up-to-date command references.

### 5. Help Command Not Showing Expected Options

**Problem**: Looking for `traefik` in help output

```bash
$ ichrisbirch help
# traefik commands not listed
```

**Root Cause**: This is **correct behavior** - simplified CLI only shows available commands

**Resolution**: The help output is correct. Use environment-specific help

```bash
# General help (shows all top-level commands)
ichrisbirch help

# Environment-specific help
ichrisbirch dev help

# SSL manager help
ichrisbirch ssl-manager help
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
./deploy.sh: line 15: ichrisbirch traefik start dev: command failed
```

**Root Cause**: Scripts written for the old duplicated CLI interface

**Resolution**: Update scripts to use simplified commands

```bash
# WRONG (will fail)
#!/bin/bash
ichrisbirch traefik start dev
ichrisbirch traefik health dev

# CORRECT (current)
#!/bin/bash
ichrisbirch dev start
ichrisbirch dev health
```

**Prevention**: Update all automation scripts and CI/CD pipelines to use the new simplified interface.

## 🔧 Advanced CLI Debugging

### Check CLI Installation

```bash
# Verify CLI is executable
ls -la ./cli/ichrisbirch

# Make executable if needed
chmod +x ./cli/ichrisbirch

# Test basic functionality
./cli/ichrisbirch help
```

### Verify Current CLI Version

```bash
# Check CLI script for version information
head -20 ./cli/ichrisbirch

# Look for the function definitions to confirm simplified interface
grep -n "function.*start\|function.*traefik" ./cli/ichrisbirch
```

### Debug Command Parsing

```bash
# Enable bash debugging to see command parsing
bash -x ./cli/ichrisbirch dev start

# Check if commands are being recognized
./cli/ichrisbirch dev help
```

## 🚀 CLI Migration Guide

### For Individual Users

1. **Update muscle memory**: Practice using `<env> <action>` pattern
2. **Update bookmarks**: Replace any documented commands with new syntax
3. **Check scripts**: Update any personal scripts or aliases
4. **Use help commands**: Rely on `ichrisbirch help` for current command reference

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
ichrisbirch traefik start dev    # Started dev environment
ichrisbirch dev start            # Also started dev environment (same result)

# Problems:
# - Confusion about which command to use
# - Implementation details exposed (Traefik)
# - Inconsistent command patterns
# - More commands to remember
```

**After (Clean & Professional)**:

```bash
# One command per operation
ichrisbirch dev start            # Clear, simple, consistent

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
# Environment Management (all use Traefik + HTTPS automatically)
ichrisbirch dev start           # Start development
ichrisbirch dev stop            # Stop development  
ichrisbirch dev restart         # Restart development
ichrisbirch dev status          # Status + URLs
ichrisbirch dev logs            # View logs
ichrisbirch dev health          # Health checks

ichrisbirch testing start       # Start testing
ichrisbirch testing stop        # Stop testing
ichrisbirch testing restart     # Restart testing
ichrisbirch testing status      # Status + URLs
ichrisbirch testing logs        # View logs
ichrisbirch testing health      # Health checks

ichrisbirch prod start          # Start production
ichrisbirch prod stop           # Stop production
ichrisbirch prod restart        # Restart production
ichrisbirch prod status         # Status + URLs
ichrisbirch prod logs           # View logs
ichrisbirch prod health         # Health checks

# SSL Certificate Management (top-level commands)
ichrisbirch ssl-manager generate dev    # Generate certificates
ichrisbirch ssl-manager info dev        # Certificate information
ichrisbirch ssl-manager validate dev    # Validate certificates
ichrisbirch ssl-manager help            # SSL manager help

# Help Commands
ichrisbirch help                # General help
ichrisbirch dev help            # Development help
ichrisbirch ssl-manager help    # SSL help
```

### Removed Commands (Do Not Use)

```bash
# THESE COMMANDS NO LONGER EXIST:
ichrisbirch traefik start <env>     # REMOVED
ichrisbirch traefik stop <env>      # REMOVED
ichrisbirch traefik restart <env>   # REMOVED
ichrisbirch traefik status <env>    # REMOVED
ichrisbirch traefik logs <env>      # REMOVED
ichrisbirch traefik health <env>    # REMOVED
```

The CLI simplification provides a clean, professional interface that eliminates confusion and follows modern CLI design principles. The new simplified commands are more intuitive, easier to remember, and provide a better developer experience.
