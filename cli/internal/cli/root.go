// Package cli wires the icb command tree.
package cli

import (
	"context"
	"errors"
	"fmt"
	"os"

	"github.com/datapointchris/goclikit"
	"github.com/datapointchris/goselfupdate/autoupdate"
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

// asNamespace marks a group with no action of its own, the root included. A
// bare one shows help and exits 0. A word naming none of its subcommands exits
// 2 naming the ones near it, with or without a flag after the word.
//
// Here rather than in each command file for the reason withNotFoundHints is:
// this package's files import goclikit in one place.
func asNamespace(cmd *cobra.Command) *cobra.Command {
	return goclikit.AsNamespace(cmd)
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

// noArgs refuses a positional on a leaf that takes none. Cobra's NoArgs calls
// the word an unknown command, which names a subcommand a leaf never had.
func noArgs(cmd *cobra.Command, args []string) error {
	if len(args) == 0 {
		return nil
	}
	refusal := fmt.Sprintf("%s takes no arguments, and was given %q\n\nRun '%s --help' for its flags.",
		cmd.CommandPath(), args[0], cmd.CommandPath())
	return usageError{errors.New(refusal)}
}

// argumentBelongsTo refuses a positional on a leaf that takes that value
// through flag, and spells the command line that passes it there. It is for a
// leaf whose siblings take the same value positionally, which is what makes
// the positional the natural guess.
func argumentBelongsTo(flag, purpose string) cobra.PositionalArgs {
	return func(cmd *cobra.Command, args []string) error {
		if len(args) == 0 {
			return nil
		}
		refusal := fmt.Sprintf("%s takes no arguments, and was given %q\n\n%s: %s %s %s",
			cmd.CommandPath(), args[0], purpose, cmd.CommandPath(), flag, shellQuote(args[0]))
		return usageError{errors.New(refusal)}
	}
}

func NewRootCommand() *cobra.Command {
	root := asNamespace(&cobra.Command{
		Use:   "icb",
		Short: "icb — the ichrisbirch data CLI",
		Long: "icb reads and edits the ichrisbirch personal-productivity apps — tasks,\n" +
			"projects, issues, books, articles, habits, recipes, countdowns, events, and\n" +
			"strains.\n" +
			"\n" +
			"Start with `icb overview` for what is outstanding in every app at once.\n" +
			"Each section stops at ten rows, so the one that caught your eye continues\n" +
			"under its own noun: `icb tasks list`, `icb issues next`.\n" +
			"\n" +
			"Development work is `icb issues`, and `icb issues next` is the order to\n" +
			"take it in. `icb projects` holds personal projects, never development work.\n" +
			"\n" +
			"The noun comes first and the verb last: `icb books list` becomes\n" +
			"`icb books edit`. Every read verb takes --json. Run any partial command\n" +
			"bare to see what comes next. Authenticate once with `icb auth login`.",
		Example: "  icb overview\n" +
			"  icb issues next --repo ichrisbirch --limit 1\n" +
			"  icb issues show 42\n" +
			"  icb habits complete 5\n" +
			"  icb tasks create --name \"Renew registration\" --category chore --window-days 14",
		Version:       version,
		SilenceUsage:  true, // usage is shown deliberately, not on every runtime error
		SilenceErrors: true, // Execute prints errors itself, to stderr
		// ArbitraryArgs lets an unknown top-level command (`icb nope`) reach the
		// namespace's own refusal, marked as a usage error (exit 2). Cobra's
		// default root validator (legacyArgs) instead returns its own unmarked
		// "unknown command" error (exit 1). Subcommands, having a parent, are
		// exempt from that validator.
		Args: cobra.ArbitraryArgs,
	})
	// Flag mistakes become usageError → exit 2. Inherited by subcommands.
	// goclikit.Execute composes with this rather than replacing it, and keeping
	// it here is what makes the tree self-classifying for anything driving
	// NewRootCommand directly.
	root.SetFlagErrorFunc(func(_ *cobra.Command, err error) error {
		return usageError{err}
	})

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
	root.AddCommand(newIssuesCommand())
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
	root.AddCommand(newStrainsCommand())

	// After the tree is assembled: cobra only propagates a usage template to
	// commands that already exist when it is set.
	applyUsageTemplate(root)
	return root
}

// Execute runs the command tree, prints any error to stderr, and returns the
// process exit code.
func Execute() int {
	err := run(NewRootCommand(), autoupdate.Config{Update: updateConfig()})

	// An exitCode carries its own code and an empty message, so it is not printed
	// as an "error:" line — it reports a valid non-success state (e.g. "not logged
	// in") rather than a failure.
	// `update` writes its own ✓/✗ line, so printing here would report the same
	// failure twice.
	var ec exitCode
	if err != nil && !errors.As(err, &ec) && !errors.Is(err, goclikit.ErrReported) {
		fmt.Fprintln(os.Stderr, "error:", err)
	}
	return exitCodeFor(err)
}

// run drives root through the shared bootstrap and returns its error.
//
// Separate from Execute, and taking the update config, so a test can drive the
// real tree with the version check suppressed and read the error rather than an
// exit code. WithNotFound is the whole of the not-found feature's wiring: drop
// it and every 404 prints the API's status line again, which is what
// TestA404FromTheRealTreeCarriesItsRecoveryHints catches.
func run(root *cobra.Command, config autoupdate.Config) error {
	return goclikit.Execute(context.Background(), root, config, goclikit.WithNotFound(notFound))
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
	if errors.Is(err, goclikit.ErrUsage) {
		return 2
	}
	return 1
}
