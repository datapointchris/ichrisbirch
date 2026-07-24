// Package cli wires the icb command tree.
package cli

import (
	"errors"
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

// version is overridden at build time via -ldflags.
var version = "dev"

// usageError marks an invocation mistake (bad flag/args) so Execute can return
// exit code 2, distinct from a runtime failure (1). Per CLI conventions.
type usageError struct{ err error }

func (u usageError) Error() string { return u.err.Error() }

// exitCode lets a command choose the process exit code without Execute printing
// an "error:" line — used by `auth status` to report "not logged in" (exit 1) as
// a valid state, not a failure.
type exitCode int

func (e exitCode) Error() string { return "" }

// requireSubcommand is the RunE for group commands (root, auth) that have no
// action of their own: a bare invocation shows help (exit 0), but an unknown
// subcommand is a usage error (exit 2) rather than cobra's default of silently
// showing help.
func requireSubcommand(cmd *cobra.Command, args []string) error {
	if len(args) == 0 {
		return cmd.Help()
	}
	return usageError{fmt.Errorf("unknown command %q for %q\nRun '%s --help' for usage",
		args[0], cmd.CommandPath(), cmd.CommandPath())}
}

// usageArgs wraps a positional-args validator so a violation (wrong count, etc.)
// surfaces as a usageError → exit 2, matching how flag errors are classified.
// Cobra's built-in validators return plain errors that would otherwise exit 1.
func usageArgs(validate cobra.PositionalArgs) cobra.PositionalArgs {
	return func(cmd *cobra.Command, args []string) error {
		if err := validate(cmd, args); err != nil {
			return usageError{err}
		}
		return nil
	}
}

func NewRootCommand() *cobra.Command {
	root := &cobra.Command{
		Use:   "icb",
		Short: "icb — the ichrisbirch data CLI",
		Long: "icb is the command-line client for the ichrisbirch personal-productivity\n" +
			"apps (tasks, projects, countdowns, books, articles, habits, events).\n" +
			"Authenticate once with `icb auth login`, then run commands against the API\n" +
			"as yourself.",
		Version:       version,
		SilenceUsage:  true, // usage is shown deliberately, not on every runtime error
		SilenceErrors: true, // Execute prints errors itself, to stderr
		// ArbitraryArgs lets an unknown top-level command (`icb nope`) reach
		// requireSubcommand → a typed usageError (exit 2). Cobra's default root
		// validator (legacyArgs) instead returns its own untyped "unknown
		// command" error (exit 1); subcommands, having a parent, are exempt from
		// that validator and already route through requireSubcommand.
		Args: cobra.ArbitraryArgs,
		RunE: requireSubcommand,
	}
	// Flag mistakes become usageError → exit 2. Inherited by subcommands.
	root.SetFlagErrorFunc(func(_ *cobra.Command, err error) error { return usageError{err} })

	// Free -v for a future --verbose flag: cobra's auto version flag claims -v,
	// but the CLI convention reserves -v for verbose and -V/--version for
	// version. Drop the auto shorthand so --version stays long-only for now.
	root.InitDefaultVersionFlag()
	if f := root.Flags().Lookup("version"); f != nil {
		f.Shorthand = ""
	}

	root.AddCommand(newAuthCommand())
	return root
}

// Execute runs the command tree, prints any error to stderr, and returns the
// process exit code.
func Execute() int {
	root := NewRootCommand()
	err := root.Execute()

	// An exitCode carries its own code and an empty message, so it is not printed
	// as an "error:" line — it reports a valid non-success state (e.g. "not logged
	// in") rather than a failure.
	var ec exitCode
	if err != nil && !errors.As(err, &ec) {
		fmt.Fprintln(os.Stderr, "error:", err)
	}
	return exitCodeFor(err)
}

// exitCodeFor maps a command error to a process exit code: 0 success, 2 for a
// usage mistake (bad flag/args), an explicit exitCode's own value, else 1 for a
// runtime failure. Pure so it can be unit-tested without running the tree.
func exitCodeFor(err error) int {
	if err == nil {
		return 0
	}
	var ec exitCode
	if errors.As(err, &ec) {
		return int(ec)
	}
	var usageErr usageError
	if errors.As(err, &usageErr) {
		return 2
	}
	return 1
}
