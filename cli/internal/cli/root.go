// Package cli wires the icb command tree.
package cli

import (
	"context"
	"errors"
	"fmt"
	"os"

	"github.com/datapointchris/goselfupdate/autoupdate"
	"github.com/datapointchris/goselfupdate/cobracmd"
	"github.com/spf13/cobra"
)

// version is overridden at build time via -ldflags.
var version = "dev"

// noInput is bound to the persistent --no-input flag, which forces the
// non-interactive path from a terminal. Package-level because every destructive
// verb consults it through confirm; pflag rewrites it to the default on each
// NewRootCommand, so a test never inherits the previous one's value.
var noInput bool

// usageError marks an invocation mistake (bad flag/args) so Execute can return
// exit code 2, distinct from a runtime failure (1). Per CLI conventions.
type usageError struct{ err error }

func (u usageError) Error() string { return u.err.Error() }

// Unwrap exposes the wrapped cause, so a caller can branch on a sentinel with
// errors.Is instead of matching the rendered message.
func (u usageError) Unwrap() error { return u.err }

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
		Long: "icb reads and edits the ichrisbirch personal-productivity apps — tasks,\n" +
			"projects, books, articles, habits, recipes, countdowns, and events.\n" +
			"\n" +
			"The noun comes first and the verb last, so moving from reading a resource\n" +
			"to acting on it changes only the final word: `icb books list` becomes\n" +
			"`icb books edit`. Every read verb takes --json.\n" +
			"\n" +
			"Run any partial command with no arguments or --help to see what comes\n" +
			"next. Authenticate once with `icb auth login`.",
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
	// cobracmd.Execute composes with this rather than replacing it, and keeping
	// it here is what makes the tree self-classifying for anything driving
	// NewRootCommand directly.
	root.SetFlagErrorFunc(func(_ *cobra.Command, err error) error { return usageError{err} })

	root.PersistentFlags().BoolVar(&noInput, "no-input", false,
		"Never prompt; fail naming the flag that would have answered")

	// Free -v for a future --verbose flag: cobra's auto version flag claims -v,
	// but the CLI convention reserves -v for verbose and -V/--version for
	// version. Drop the auto shorthand so --version stays long-only for now.
	root.InitDefaultVersionFlag()
	if f := root.Flags().Lookup("version"); f != nil {
		f.Shorthand = ""
	}

	root.AddCommand(newAuthCommand())
	root.AddCommand(newUpdateCommand())
	root.AddCommand(newOverviewCommand())
	root.AddCommand(newProjectsCommand())
	root.AddCommand(newTasksCommand())
	root.AddCommand(newAutotasksCommand())
	root.AddCommand(newCountdownsCommand())
	root.AddCommand(newEventsCommand())
	root.AddCommand(newHabitsCommand())
	root.AddCommand(newPatternsCommand())
	root.AddCommand(newBooksCommand())
	root.AddCommand(newArticlesCommand())
	root.AddCommand(newRecipesCommand())
	root.AddCommand(newCookingTechniquesCommand())

	// After the tree is assembled: cobra only propagates a usage template to
	// commands that already exist when it is set, and the RunE wrapper has to
	// see every command's own RunE.
	applyUsageTemplate(root)
	attachNotFoundHints(root)
	return root
}

// Execute runs the command tree, prints any error to stderr, and returns the
// process exit code.
func Execute() int {
	root := NewRootCommand()
	err := cobracmd.Execute(context.Background(), root, autoupdate.Config{Update: updateConfig()})

	// An exitCode carries its own code and an empty message, so it is not printed
	// as an "error:" line — it reports a valid non-success state (e.g. "not logged
	// in") rather than a failure.
	// `update` writes its own ✓/✗ line, so printing here would report the same
	// failure twice.
	var ec exitCode
	if err != nil && !errors.As(err, &ec) && !errors.Is(err, cobracmd.ErrReported) {
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
	// The library's classification, for a usage mistake cobra rejects before
	// any RunE runs and the tree therefore never marks itself.
	if errors.Is(err, cobracmd.ErrUsage) {
		return 2
	}
	return 1
}
