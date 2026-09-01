package cli

import (
	"testing"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
)

// The server derives the status, so the table prints what the wire says rather
// than recomputing it. That is what keeps the table and --json from disagreeing
// about one item.
func TestServerStatus_PrefersTheWireValue(t *testing.T) {
	if got := serverStatus(api.ItemStatusArchived, false, false); got != api.ItemStatusArchived {
		t.Errorf("serverStatus = %q, want the wire value %q", got, api.ItemStatusArchived)
	}
}

// An API that does not send the field yet leaves it empty once decoded, and the
// booleans still answer — `api-design.md` § "Clients branch on `nil`, never on
// \"empty\"". Without this the column would blank for the minutes between a CLI
// release and the API deploy.
func TestServerStatus_FallsBackToTheBooleans(t *testing.T) {
	cases := []struct {
		name      string
		archived  bool
		completed bool
		want      string
	}{
		{"neither is open", false, false, api.ItemStatusOpen},
		{"completed alone is completed", false, true, api.ItemStatusCompleted},
		{"archived alone is archived", true, false, api.ItemStatusArchived},
		{"archived beats completed", true, true, api.ItemStatusArchived},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			if got := serverStatus("", c.archived, c.completed); got != c.want {
				t.Errorf("serverStatus(\"\", %v, %v) = %q, want %q", c.archived, c.completed, got, c.want)
			}
		})
	}
}

// The three item views render the same word through the same path, so a status
// cannot come out differently depending on which command asked.
func TestEveryItemViewRendersTheServerStatus(t *testing.T) {
	const want = api.ItemStatusCompleted
	if got := flatItemStatus(api.ProjectItem{Status: want}); got != want {
		t.Errorf("flatItemStatus = %q, want %q", got, want)
	}
	if got := detailStatus(api.ProjectItemDetail{Status: want}); got != want {
		t.Errorf("detailStatus = %q, want %q", got, want)
	}
	if got := itemStatus(api.ProjectItemInProject{Status: want}); got != want {
		t.Errorf("itemStatus = %q, want %q", got, want)
	}
}

// A task has no archived state and the API sends it no status, so it keeps
// deriving from its own boolean.
func TestTaskStateStillDerives(t *testing.T) {
	if got := taskState(api.ProjectItemTask{Completed: true}); got != api.ItemStatusCompleted {
		t.Errorf("taskState = %q, want %q", got, api.ItemStatusCompleted)
	}
	if got := taskState(api.ProjectItemTask{Completed: false}); got != api.ItemStatusOpen {
		t.Errorf("taskState = %q, want %q", got, api.ItemStatusOpen)
	}
}
