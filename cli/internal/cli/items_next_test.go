package cli

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
)

var (
	readingBacklog = api.Project{ID: "reading", Name: "Reading backlog", Kind: "life", Status: api.ProjectStatusActive, Position: 0, CreatedAt: fixedNow.AddDate(0, 0, -60)}
	sellProject    = api.Project{ID: "sell", Name: "Sell Unused Shite", Kind: "life", Status: api.ProjectStatusActive, Position: 90, CreatedAt: fixedNow.AddDate(0, 0, -200)}
)

func queuedIn(project api.Project, id string, number int, position int) api.ProjectItem {
	return api.ProjectItem{
		ID: id, Number: number, Title: "item " + id, CreatedAt: fixedNow.AddDate(0, 0, -number),
		Projects:    []api.Project{project},
		Memberships: []api.ProjectItemMembership{{ProjectID: project.ID, Position: position}},
	}
}

type itemsNextRun struct {
	stdout string
	stderr string
	runErr error
}

func runItemsNext(t *testing.T, open []api.ProjectItem, blocked []api.ProjectItem, args ...string) itemsNextRun {
	t.Helper()
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		rows := open
		if r.URL.Path == "/project-items/blocked/" {
			rows = blocked
		}
		_ = json.NewEncoder(w).Encode(rows)
	}))
	t.Cleanup(server.Close)
	asService(t, serviceIDP(t).URL, server.URL, serviceSecret)

	root := NewRootCommand()
	var stdout, stderr bytes.Buffer
	root.SetOut(&stdout)
	root.SetErr(&stderr)
	root.SetArgs(append([]string{"projects", "items", "next"}, args...))
	runErr := root.Execute()
	return itemsNextRun{stdout: stdout.String(), stderr: stderr.String(), runErr: runErr}
}

func TestItemsNext_ListsTheFocusProjectAloneAndSaysWhatTheCapCut(t *testing.T) {
	open := []api.ProjectItem{
		queuedIn(sellProject, "s1", 11, 0),
		queuedIn(readingBacklog, "r2", 22, 1),
		queuedIn(readingBacklog, "r1", 21, 0),
	}

	run := runItemsNext(t, open, nil, "-n", "1")

	if run.runErr != nil {
		t.Fatalf("run: %v", run.runErr)
	}
	if !strings.HasPrefix(run.stdout, "Reading backlog\n") {
		t.Errorf("stdout = %q, want the focus project named first", run.stdout)
	}
	if !strings.Contains(run.stdout, "item r1") || strings.Contains(run.stdout, "item r2") {
		t.Errorf("stdout = %q, want only the head of the focus queue under -n 1", run.stdout)
	}
	if strings.Contains(run.stdout, "item s1") {
		t.Errorf("stdout = %q, want no item from a project outside the focus", run.stdout)
	}
	if !strings.Contains(run.stderr, "1 of 2 shown: -n 2 shows the rest") {
		t.Errorf("stderr = %q, want the cut counted against the focus project's queue", run.stderr)
	}
}

func TestItemsNext_JSONCarriesNoNote(t *testing.T) {
	open := []api.ProjectItem{queuedIn(readingBacklog, "r1", 21, 0), queuedIn(readingBacklog, "r2", 22, 1)}

	run := runItemsNext(t, open, nil, "-n", "1", "--json")

	var items []api.ProjectItem
	if err := json.Unmarshal([]byte(run.stdout), &items); err != nil {
		t.Fatalf("stdout is not JSON: %v\n%s", err, run.stdout)
	}
	if len(items) != 1 || items[0].ID != "r1" {
		t.Errorf("--json items = %s, want r1 alone", itemIDs(items))
	}
	if run.stderr != "" {
		t.Errorf("stderr = %q, want silence under --json", run.stderr)
	}
}

func TestItemsNext_ABlockedFocusProjectListsWhatBlocksItInsteadOfMovingOn(t *testing.T) {
	stuck := queuedIn(readingBacklog, "r1", 21, 0)
	open := []api.ProjectItem{stuck, queuedIn(sellProject, "s1", 11, 0)}

	run := runItemsNext(t, open, []api.ProjectItem{stuck})

	if run.runErr != nil {
		t.Fatalf("run: %v", run.runErr)
	}
	if !strings.Contains(run.stdout, "Reading backlog: nothing to take, every open item is blocked.") {
		t.Errorf("stdout = %q, want the focus project kept and named as blocked", run.stdout)
	}
	if !strings.Contains(run.stdout, "item r1") {
		t.Errorf("stdout = %q, want the blocked item listed", run.stdout)
	}
	if strings.Contains(run.stdout, "item s1") {
		t.Errorf("stdout = %q, want the next project's items held back", run.stdout)
	}
}
