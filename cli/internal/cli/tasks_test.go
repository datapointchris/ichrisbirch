package cli

import (
	"strings"
	"testing"
)

// An unknown category is refused before any call is made, so a typo costs a
// usage error rather than an empty list that reads as "nothing in there".
func TestTasksList_UnknownCategoryIsAUsageError(t *testing.T) {
	if code := runTree(t, "tasks", "list", "--category", "Persona"); code != 2 {
		t.Errorf("exit code = %d, want 2", code)
	}
}

// The same validator `create` and `edit` use, so a spelling one door accepts is
// accepted by all three rather than each having its own idea of the table.
func TestTasksList_CategoryIsCanonicalisedNotJustAccepted(t *testing.T) {
	canonical, err := taskCategory("personal")
	if err != nil {
		t.Fatalf("taskCategory(personal): %v", err)
	}
	if canonical != "Personal" {
		t.Errorf("taskCategory(personal) = %q, want Personal", canonical)
	}
}

func TestTasksList_AnUnknownCategoryNamesTheNearOnes(t *testing.T) {
	_, err := taskCategory("Persona")
	if err == nil {
		t.Fatal("taskCategory(Persona) returned no error")
	}
	if !strings.Contains(err.Error(), "Personal") {
		t.Errorf("error = %q, want it to name Personal", err)
	}
}
