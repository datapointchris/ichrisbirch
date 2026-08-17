package prompt

import (
	"bytes"
	"errors"
	"io"
	"strings"
	"testing"
)

var categories = []string{"Automotive", "Chore", "Computer", "Dingo"}

// run drives a form with typed lines and returns the answers plus everything the
// form said.
func run(t *testing.T, form Form, typed string) (Answers, string) {
	t.Helper()
	var out bytes.Buffer
	answers, err := form.Run(NewPlainSession(strings.NewReader(typed), &out))
	if err != nil {
		t.Fatalf("Run: %v", err)
	}
	return answers, out.String()
}

func taskForm() Form {
	return Form{
		Fields: []Field{
			{Key: "name", Label: "Name"},
			{Key: "category", Label: "Category", Choices: categories, Validate: OneOf(categories)},
			{Key: "priority", Label: "Priority", Default: "1", Validate: Int},
			{Key: "notes", Label: "Notes", Optional: true},
		},
	}
}

func TestForm_AsksEveryFieldInOrder(t *testing.T) {
	answers, out := run(t, taskForm(), "Renew registration\nChore\n3\nby friday\n")

	want := Answers{"name": "Renew registration", "category": "Chore", "priority": "3", "notes": "by friday"}
	for key, value := range want {
		if answers.Get(key) != value {
			t.Errorf("answers[%q] = %q, want %q", key, answers.Get(key), value)
		}
	}
	if got := strings.Index(out, "Name:"); got > strings.Index(out, "Category:") {
		t.Error("Category was asked before Name — fields are asked in the order they are declared")
	}
}

func TestForm_RejectedAnswerComesBackAndNothingElseIsLost(t *testing.T) {
	answers, out := run(t, taskForm(), "Renew registration\nChorre\nChore\n3\n\n")

	if answers.Get("name") != "Renew registration" {
		t.Errorf("name = %q, want it kept — a bad category must not cost the fields already typed", answers.Get("name"))
	}
	if answers.Get("category") != "Chore" {
		t.Errorf("category = %q, want the corrected value", answers.Get("category"))
	}
	if !strings.Contains(out, `unknown value "Chorre"`) {
		t.Errorf("output did not name the rejected value:\n%s", out)
	}
	if !strings.Contains(out, `(was "Chorre")`) {
		t.Errorf("the rejected answer was not offered back for correction:\n%s", out)
	}
	if strings.Contains(out, "Name:(was") {
		t.Error("Name was re-asked — only the rejected field is asked again")
	}
}

func TestForm_EmptyAnswerTakesTheDefault(t *testing.T) {
	answers, out := run(t, taskForm(), "Renew\nChore\n\n\n")

	if answers.Get("priority") != "1" {
		t.Errorf("priority = %q, want the default 1", answers.Get("priority"))
	}
	if !strings.Contains(out, "Priority [1]:") {
		t.Errorf("the prompt did not show the default:\n%s", out)
	}
}

func TestForm_SkippedOptionalFieldIsAbsent(t *testing.T) {
	answers, out := run(t, taskForm(), "Renew\nChore\n2\n\n")

	if answers.Has("notes") {
		t.Errorf("notes = %q, want it absent — skipped is not the same as set to empty", answers.Get("notes"))
	}
	if !strings.Contains(out, "Notes (optional):") {
		t.Errorf("the prompt did not mark the field skippable:\n%s", out)
	}
}

func TestForm_RequiredFieldIsAskedAgainWhenEmpty(t *testing.T) {
	answers, out := run(t, taskForm(), "\nRenew\nChore\n1\n\n")

	if answers.Get("name") != "Renew" {
		t.Errorf("name = %q, want the answer given after the empty one", answers.Get("name"))
	}
	if !strings.Contains(out, "Name is required.") {
		t.Errorf("output did not say the field is required:\n%s", out)
	}
}

func TestForm_ListsTheChoicesBeforeAsking(t *testing.T) {
	_, out := run(t, taskForm(), "Renew\nChore\n1\n\n")

	if !strings.Contains(out, "Category is one of:") {
		t.Errorf("the choices were not introduced:\n%s", out)
	}
	for _, category := range categories {
		if !strings.Contains(out, category) {
			t.Errorf("choice %q was not listed:\n%s", category, out)
		}
	}
	if strings.Contains(out, "Tab") {
		t.Error("a session that cannot complete must not advertise Tab")
	}
}

func TestForm_CanceledInputReturnsEOF(t *testing.T) {
	var out bytes.Buffer
	answers, err := taskForm().Run(NewPlainSession(strings.NewReader("Renew\n"), &out))

	if !errors.Is(err, io.EOF) {
		t.Fatalf("err = %v, want io.EOF", err)
	}
	if answers != nil {
		t.Errorf("answers = %v, want none — a half-filled record is not a record", answers)
	}
}

func TestForm_IntRejectsAWordAndKeepsIt(t *testing.T) {
	answers, out := run(t, taskForm(), "Renew\nChore\nhigh\n2\n\n")

	if answers.Get("priority") != "2" {
		t.Errorf("priority = %q, want the corrected value", answers.Get("priority"))
	}
	if !strings.Contains(out, `"high" is not a whole number`) {
		t.Errorf("output did not explain the rejection:\n%s", out)
	}
}

func TestAnswers_MergeKeepsWhatIsAlreadyThere(t *testing.T) {
	answers := Answers{"name": "from the flag"}
	answers.Merge(Answers{"name": "from the prompt", "category": "Chore"})

	if answers.Get("name") != "from the flag" {
		t.Errorf("name = %q, want the flag to outrank the prompt", answers.Get("name"))
	}
	if answers.Get("category") != "Chore" {
		t.Errorf("category = %q, want the prompt to fill what the flags left out", answers.Get("category"))
	}
}

func TestOneOf_MatchesCaseInsensitivelyAndReturnsTheListSpelling(t *testing.T) {
	value, err := OneOf(categories)("chore")
	if err != nil {
		t.Fatalf("OneOf rejected a known value: %v", err)
	}
	if value != "Chore" {
		t.Errorf("value = %q, want the spelling the list carries", value)
	}
}

func TestOneOf_RejectionNamesEveryAcceptedValue(t *testing.T) {
	_, err := OneOf(categories)("nope")
	if err == nil {
		t.Fatal("OneOf accepted a value that is not in the list")
	}
	for _, category := range categories {
		if !strings.Contains(err.Error(), category) {
			t.Errorf("error = %q, want it to name %q", err, category)
		}
	}
}

func TestInt_TrimsToTheParsedNumber(t *testing.T) {
	value, err := Int("007")
	if err != nil {
		t.Fatalf("Int rejected a number: %v", err)
	}
	if value != "7" {
		t.Errorf("value = %q, want the parsed form", value)
	}
}
