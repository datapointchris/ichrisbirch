package cli

import (
	"errors"
	"net/http"
	"slices"
	"strings"
	"testing"

	"github.com/spf13/cobra"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
)

// notFound is the error shape the api package produces for a 404, with the
// subject the API reports.
func notFound(subject string) error {
	return &api.APIError{StatusCode: http.StatusNotFound, Status: "404 Not Found", Message: subject}
}

// findCommand resolves a command path against the real assembled tree, so a
// test asserts on what `icb` actually runs rather than a fixture of it.
func findCommand(t *testing.T, path ...string) *cobra.Command {
	t.Helper()
	cmd, _, err := NewRootCommand().Find(path)
	if err != nil {
		t.Fatalf("Find(%v): %v", path, err)
	}
	if strings.Join(path, " ") != strings.TrimPrefix(cmd.CommandPath(), "icb ") {
		t.Fatalf("Find(%v) resolved to %q", path, cmd.CommandPath())
	}
	return cmd
}

func TestHintNotFound_NamesTheSubjectAndBothWaysToFindAnItem(t *testing.T) {
	err := hintNotFound(findCommand(t, "projects", "items", "show"), notFound("project item 999999 not found"))

	got := err.Error()
	for _, want := range []string{
		"project item 999999 not found",
		"icb projects items search <query>",
		"icb projects items list --status all",
	} {
		if !strings.Contains(got, want) {
			t.Errorf("error = %q, want it to name %q", got, want)
		}
	}
}

// The transport prefix reports how the answer arrived. A 404 is an answer, and
// the line is read by someone who wants the next command rather than the status
// code that produced it.
func TestHintNotFound_DropsTheTransportPrefix(t *testing.T) {
	err := hintNotFound(findCommand(t, "projects", "items", "show"), notFound("project item 999999 not found"))

	if strings.Contains(err.Error(), "API request failed") {
		t.Errorf("error = %q, want no transport prefix", err)
	}
}

// `icb projects items` sits under `icb projects` and acts on a different
// resource, so the closed-projects line would send the caller after the wrong
// thing.
func TestHintNotFound_AnItemDoesNotNameTheProjectRecovery(t *testing.T) {
	err := hintNotFound(findCommand(t, "projects", "items", "show"), notFound("project item 999999 not found"))

	if strings.Contains(err.Error(), "icb projects list") {
		t.Errorf("error = %q, want the project hint left out", err)
	}
}

func TestHintNotFound_AProjectNamesTheStatesThatHideOne(t *testing.T) {
	err := hintNotFound(findCommand(t, "projects", "show"), notFound("project nope not found"))

	if !strings.Contains(err.Error(), "icb projects list --status all") {
		t.Errorf("error = %q, want the widening hint", err)
	}
}

// A proxy error page or an Authelia redirect decodes to a status and no
// message, so the resource was never reached. Claiming one is missing would
// send the caller searching for a row that is probably there, and the two
// causes have different remedies.
func TestHintNotFound_LeavesABodylessNotFoundAlone(t *testing.T) {
	cause := &api.APIError{StatusCode: http.StatusNotFound, Status: "404 Not Found"}

	got := hintNotFound(findCommand(t, "projects", "items", "show"), cause)

	if got != error(cause) {
		t.Fatalf("hintNotFound = %v, want the error returned untouched", got)
	}
	if !strings.Contains(got.Error(), "404 Not Found") {
		t.Errorf("error = %q, want the status kept", got)
	}
}

// complete-task takes two ids and the API names which one was missing, so the
// error has to carry the way in to both.
func TestHintNotFound_ATaskVerbNamesTheItemAndTheTaskList(t *testing.T) {
	err := hintNotFound(findCommand(t, "projects", "items", "complete-task"), notFound("project item task 4 not found"))

	got := err.Error()
	for _, want := range []string{
		"icb projects items search <query>",
		"icb projects items tasks <item>",
	} {
		if !strings.Contains(got, want) {
			t.Errorf("error = %q, want it to name %q", got, want)
		}
	}
}

func TestHintNotFound_AMembershipVerbNamesTheProjectList(t *testing.T) {
	err := hintNotFound(findCommand(t, "projects", "items", "add-project"), notFound("project nope not found"))

	if !strings.Contains(err.Error(), "icb projects list --status all") {
		t.Errorf("error = %q, want the project hint on a verb that takes a project", err)
	}
}

func TestHintNotFound_LeavesEverythingThatIsNotA404Alone(t *testing.T) {
	cmd := findCommand(t, "projects", "items", "show")
	for _, cause := range []error{
		errors.New("boom"),
		&api.APIError{StatusCode: http.StatusUnauthorized, Status: "401 Unauthorized", Message: "nope"},
	} {
		if got := hintNotFound(cmd, cause); got != cause {
			t.Errorf("hintNotFound(%v) = %v, want the error returned untouched", cause, got)
		}
	}
}

// auth has no id to look up, so a 404 there has no recovery command to name and
// is left as it was.
func TestHintNotFound_LeavesA404WithNoHintsAlone(t *testing.T) {
	cause := notFound("thing 1 not found")
	if got := hintNotFound(findCommand(t, "auth", "status"), cause); got != cause {
		t.Errorf("hintNotFound = %v, want the error returned untouched", got)
	}
}

// The rendered message replaces the API error, so a caller branching on the
// status code has to still reach it.
func TestHintNotFound_KeepsTheAPIErrorReachable(t *testing.T) {
	err := hintNotFound(findCommand(t, "projects", "items", "show"), notFound("project item 1 not found"))

	var apiErr *api.APIError
	if !errors.As(err, &apiErr) {
		t.Fatalf("errors.As did not reach the *api.APIError in %v", err)
	}
	if !apiErr.NotFound() {
		t.Errorf("status = %d, want 404", apiErr.StatusCode)
	}
	if exitCodeFor(err) != 1 {
		t.Errorf("exit code = %d, want 1", exitCodeFor(err))
	}
}

// The hints reach the terminal by wrapping RunE once over the assembled tree,
// so the wrapping itself is what has to be proved — a 404 returned from a RunE
// comes back carrying them.
func TestAttachNotFoundHints_WrapsEveryRunEInTheTree(t *testing.T) {
	leaf := withNotFoundHints(&cobra.Command{
		Use:  "leaf",
		RunE: func(*cobra.Command, []string) error { return notFound("widget 7 not found") },
	}, "List every widget: icb widgets list")
	root := &cobra.Command{Use: "root", SilenceUsage: true, SilenceErrors: true}
	root.AddCommand(leaf)
	attachNotFoundHints(root)

	root.SetArgs([]string{"leaf"})
	err := root.Execute()
	if err == nil {
		t.Fatal("want the 404 to surface")
	}
	if !strings.Contains(err.Error(), "List every widget: icb widgets list") {
		t.Errorf("error = %q, want the hint attached by the wrapper", err)
	}
}

// resourceExempt names the top-level commands that take no resource id, so a
// missing hint set on one of them is correct rather than an oversight. Only
// commands the tree actually holds: cobra adds help and completion at Execute,
// so naming them here would read as a decision about commands that are absent.
var resourceExempt = map[string]bool{
	"auth":     true,
	"update":   true,
	"overview": true,
}

// A resource added without hints is the way this regresses: the code keeps
// working and its 404 quietly goes back to naming no next command.
func TestEveryResourceCommandCarriesNotFoundHints(t *testing.T) {
	root := NewRootCommand()
	for _, group := range root.Commands() {
		if resourceExempt[group.Name()] {
			continue
		}
		walkCommands(group, func(cmd *cobra.Command) {
			hints := notFoundHintsFor(cmd)
			if len(hints) == 0 {
				t.Errorf("%s has no not-found hints", cmd.CommandPath())
				return
			}
			for _, hint := range hints {
				_, command, found := strings.Cut(hint, ": ")
				if !found || !strings.HasPrefix(command, "icb ") {
					t.Errorf("%s hint %q is not a sentence, a colon, and an icb command",
						cmd.CommandPath(), hint)
				}
			}
		})
	}
}

func walkCommands(cmd *cobra.Command, visit func(*cobra.Command)) {
	visit(cmd)
	for _, sub := range cmd.Commands() {
		walkCommands(sub, visit)
	}
}

// The single attachNotFoundHints call in NewRootCommand is the whole feature
// reaching a terminal, and every test that calls hintNotFound directly stays
// green without it. This is what observes the call.
func TestNewRootCommand_WrapsEveryRunEItAssembles(t *testing.T) {
	walkCommands(NewRootCommand(), func(cmd *cobra.Command) {
		if cmd.RunE == nil {
			return
		}
		if cmd.Annotations[notFoundWrappedKey] != "yes" {
			t.Errorf("%s has a RunE the not-found wrapper never reached", cmd.CommandPath())
		}
	})
}

// hintCommand returns the command half of a hint — everything after the colon.
func hintCommand(t *testing.T, hint string) string {
	t.Helper()
	_, command, found := strings.Cut(hint, ": ")
	if !found {
		t.Fatalf("hint %q has no colon", hint)
	}
	return command
}

// childNamed returns the subcommand of cmd with this name, or nil.
func childNamed(cmd *cobra.Command, name string) *cobra.Command {
	for _, sub := range cmd.Commands() {
		if sub.Name() == name {
			return sub
		}
	}
	return nil
}

// A hint names a command the reader is about to type, so it has to resolve
// against the tree. Renaming a subcommand otherwise leaves the hint pointing at
// nothing, and the shape check alone stays green.
func TestEveryHintNamesACommandThatResolves(t *testing.T) {
	root := NewRootCommand()
	walkCommands(root, func(cmd *cobra.Command) {
		for _, hint := range notFoundHintsFor(cmd) {
			command := hintCommand(t, hint)
			words := strings.Fields(strings.TrimPrefix(command, "icb "))
			current, consumed := root, 0
			for _, word := range words {
				next := childNamed(current, word)
				if next == nil {
					break
				}
				current, consumed = next, consumed+1
			}
			if consumed == 0 {
				t.Errorf("%s: hint %q names no command in the tree", cmd.CommandPath(), command)
				continue
			}
			// What is left has to be a flag, its value, or a <placeholder> —
			// anything else is a word that used to name a subcommand.
			previousWasFlag := false
			for _, word := range words[consumed:] {
				isFlag := strings.HasPrefix(word, "-")
				if !isFlag && !strings.HasPrefix(word, "<") && !previousWasFlag {
					t.Errorf("%s: hint %q trails %q, which names no subcommand of %s",
						cmd.CommandPath(), command, word, current.CommandPath())
				}
				previousWasFlag = isFlag
			}
		}
	})
}

// A verb taking --project can 404 on the project, and the shape check cannot
// see that: it asks whether a command has any hints, never whether they match
// the nouns it can fail on. `items create` and `items tree` both shipped
// without a project hint and both passed the shape check.
func TestACommandTakingAProjectNamesHowToFindOne(t *testing.T) {
	walkCommands(NewRootCommand(), func(cmd *cobra.Command) {
		if cmd.Flags().Lookup("project") == nil {
			return
		}
		hints := notFoundHintsFor(cmd)
		if !slices.ContainsFunc(hints, func(h string) bool { return strings.Contains(h, "icb projects list") }) {
			t.Errorf("%s takes --project, and its hints name no way to find one: %v", cmd.CommandPath(), hints)
		}
	})
}
