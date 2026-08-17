package cli

import (
	"bytes"
	"strings"
	"testing"

	"github.com/spf13/cobra"

	"github.com/datapointchris/ichrisbirch/cli/internal/prompt"
)

// answerCommand builds a bare command carrying the create flags, so the
// flag-to-answer plumbing is testable without standing up an API client.
func answerCommand(t *testing.T, args ...string) *cobra.Command {
	t.Helper()
	cmd := &cobra.Command{Use: "test", RunE: func(*cobra.Command, []string) error { return nil }}
	cmd.Flags().String("name", "", "")
	cmd.Flags().String("category", "", "")
	cmd.Flags().Int("priority", 1, "")
	if err := cmd.ParseFlags(args); err != nil {
		t.Fatalf("ParseFlags: %v", err)
	}
	return cmd
}

func TestFlagAnswers_TakesOnlyWhatWasPassed(t *testing.T) {
	cmd := answerCommand(t, "--name", "Renew registration")

	answers := flagAnswers(cmd, "name", "category", "priority")

	if answers.Get("name") != "Renew registration" {
		t.Errorf("name = %q, want the flag's value", answers.Get("name"))
	}
	if answers.Has("category") {
		t.Error("category was answered by a flag nobody passed")
	}
	if answers.Has("priority") {
		t.Error("priority was answered by its default — an unpassed flag is a question, not an answer")
	}
}

func TestFlagAnswers_AnEmptyFlagIsNotAnAnswer(t *testing.T) {
	cmd := answerCommand(t, "--name", "")

	if flagAnswers(cmd, "name").Has("name") {
		t.Error("--name \"\" counted as an answer — there is no field it could fill")
	}
}

func TestValidateAnswers_RewritesToTheCanonicalSpelling(t *testing.T) {
	answers := prompt.Answers{"category": {"chore"}}

	if err := validateAnswers(answers, taskCreateFields()); err != nil {
		t.Fatalf("validateAnswers rejected a known category: %v", err)
	}
	if answers.Get("category") != "Chore" {
		t.Errorf("category = %q, want the lookup table's spelling", answers.Get("category"))
	}
}

func TestValidateAnswers_RejectionNamesTheFlagAndTheAcceptedValues(t *testing.T) {
	err := validateAnswers(prompt.Answers{"category": {"chorre"}}, taskCreateFields())

	if err == nil {
		t.Fatal("validateAnswers accepted a category the lookup table does not hold")
	}
	if !strings.Contains(err.Error(), "--category") {
		t.Errorf("error = %q, want it to name the flag", err)
	}
	if !strings.Contains(err.Error(), "Chore") {
		t.Errorf("error = %q, want it to list what would have worked", err)
	}
}

func TestUnanswered_DropsWhatTheFlagsSupplied(t *testing.T) {
	fields := unanswered(taskCreateFields(), prompt.Answers{"name": {"Renew"}, "priority": {"3"}})

	var keys []string
	for _, field := range fields {
		keys = append(keys, field.Key)
	}
	want := []string{"category", "notes"}
	if strings.Join(keys, ",") != strings.Join(want, ",") {
		t.Errorf("fields = %v, want %v — a flag already passed is not a question", keys, want)
	}
}

func TestMissingFlags_NamesEveryRequiredFieldNobodyAnswered(t *testing.T) {
	missing := missingFlags(prompt.Answers{"name": {"Renew"}}, "name", "category")

	if strings.Join(missing, ",") != "--category" {
		t.Errorf("missing = %v, want just --category", missing)
	}
}

func TestTasksCreate_WithoutATerminalNamesTheFlagsInsteadOfPrompting(t *testing.T) {
	noInput = false
	root := NewRootCommand()
	var out, errOut bytes.Buffer
	root.SetOut(&out)
	root.SetErr(&errOut)
	root.SetIn(strings.NewReader(""))
	root.SetArgs([]string{"tasks", "create"})

	err := root.Execute()

	if err == nil {
		t.Fatal("create returned no error — prompting a non-TTY caller blocks on a stdin that never closes")
	}
	if exitCodeFor(err) != 2 {
		t.Errorf("exit code = %d, want 2 for a usage mistake", exitCodeFor(err))
	}
	for _, flag := range []string{"--name", "--category"} {
		if !strings.Contains(err.Error(), flag) {
			t.Errorf("error = %q, want it to name %s", err, flag)
		}
	}
	if out.Len() != 0 {
		t.Errorf("stdout = %q, want nothing written before the refusal", out.String())
	}
}

func TestTasksCreate_RejectsABadCategoryBeforeReachingTheAPI(t *testing.T) {
	noInput = false
	root := NewRootCommand()
	root.SetOut(&bytes.Buffer{})
	root.SetErr(&bytes.Buffer{})
	root.SetIn(strings.NewReader(""))
	root.SetArgs([]string{"tasks", "create", "--name", "Renew", "--category", "chorre"})

	err := root.Execute()

	if err == nil {
		t.Fatal("create accepted a category the lookup table does not hold")
	}
	if exitCodeFor(err) != 2 {
		t.Errorf("exit code = %d, want 2 — a bad category is a usage mistake, not a server failure", exitCodeFor(err))
	}
	if !strings.Contains(err.Error(), "Chore") {
		t.Errorf("error = %q, want it to list the accepted categories", err)
	}
}

func TestFlagAnswers_ARepeatableFlagContributesEveryValue(t *testing.T) {
	cmd := &cobra.Command{Use: "test"}
	cmd.Flags().StringArray("project", nil, "")
	if err := cmd.ParseFlags([]string{"--project", "todoui", "--project", "fleet facts"}); err != nil {
		t.Fatalf("ParseFlags: %v", err)
	}

	got := strings.Join(flagAnswers(cmd, "project").All("project"), "|")

	if got != "todoui|fleet facts" {
		t.Errorf("project = %q, want both values in order", got)
	}
}

func TestProjectRef_AcceptsANameCaseInsensitivelyAndAUUIDUntouched(t *testing.T) {
	validate := projectRef([]string{"fleet facts — the measurement layer"})

	name, err := validate("FLEET FACTS — THE MEASUREMENT LAYER")
	if err != nil {
		t.Fatalf("a known project name was rejected: %v", err)
	}
	if name != "fleet facts — the measurement layer" {
		t.Errorf("name = %q, want the API's spelling", name)
	}

	id := "3f2504e0-4f89-11d3-9a0c-0305e82c3301"
	got, err := validate(id)
	if err != nil {
		t.Fatalf("a project id was rejected: %v — the API resolves either", err)
	}
	if got != id {
		t.Errorf("id = %q, want it passed through", got)
	}
}

func TestProjectRef_RejectsAnUnknownName(t *testing.T) {
	if _, err := projectRef([]string{"todoui sync"})("nope"); err == nil {
		t.Error("an unknown project name was accepted")
	}
}

func TestLooksLikeUUID(t *testing.T) {
	cases := map[string]bool{
		"3f2504e0-4f89-11d3-9a0c-0305e82c3301": true,
		"3F2504E0-4F89-11D3-9A0C-0305E82C3301": true,
		"3f2504e0-4f89-11d3-9a0c-0305e82c330":  false, // too short
		"3f2504e04f8911d39a0c0305e82c3301":     false, // no dashes
		"zf2504e0-4f89-11d3-9a0c-0305e82c3301": false, // not hex
		"todoui":                               false,
	}
	for value, want := range cases {
		if got := looksLikeUUID(value); got != want {
			t.Errorf("looksLikeUUID(%q) = %v, want %v", value, got, want)
		}
	}
}

func TestItemsCreate_WithoutATerminalRefusesBeforeReachingTheAPI(t *testing.T) {
	noInput = false
	t.Setenv("ICB_API_BASE", "http://127.0.0.1:9") // any call here would fail loudly
	root := NewRootCommand()
	var out bytes.Buffer
	root.SetOut(&out)
	root.SetErr(&bytes.Buffer{})
	root.SetIn(strings.NewReader(""))
	root.SetArgs([]string{"projects", "items", "create"})

	err := root.Execute()

	if err == nil {
		t.Fatal("create returned no error without a terminal")
	}
	if exitCodeFor(err) != 2 {
		t.Errorf("exit code = %d, want 2 — a missing flag is a usage mistake, not an API failure", exitCodeFor(err))
	}
	for _, flag := range []string{"--title", "--project"} {
		if !strings.Contains(err.Error(), flag) {
			t.Errorf("error = %q, want it to name %s", err, flag)
		}
	}
	if strings.Contains(err.Error(), "127.0.0.1") {
		t.Errorf("error = %q, want the local refusal to come before any request", err)
	}
	if out.Len() != 0 {
		t.Errorf("stdout = %q, want nothing written before the refusal", out.String())
	}
}
