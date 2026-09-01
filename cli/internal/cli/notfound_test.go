package cli

import (
	"errors"
	"net/http"
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

func TestHintNotFound_AProjectNamesTheClosedOnes(t *testing.T) {
	err := hintNotFound(findCommand(t, "projects", "show"), notFound("project nope not found"))

	if !strings.Contains(err.Error(), "icb projects list --status all") {
		t.Errorf("error = %q, want the closed-projects hint", err)
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
// missing hint set on one of them is correct rather than an oversight.
var resourceExempt = map[string]bool{
	"auth":       true,
	"update":     true,
	"overview":   true,
	"completion": true,
	"help":       true,
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
