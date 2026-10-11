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

type projectsNextRun struct {
	stdout string
	stderr string
	runErr error
}

func runProjectsNext(t *testing.T, open []api.ProjectItem, blocked []api.ProjectItem, args ...string) projectsNextRun {
	t.Helper()
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		rows := open
		if r.URL.Path == "/api/v1/project-items/blocked/" {
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
	root.SetArgs(append([]string{"projects", "next"}, args...))
	runErr := root.Execute()
	return projectsNextRun{stdout: stdout.String(), stderr: stderr.String(), runErr: runErr}
}

func TestProjectsNext_ListsTheFocusProjectAloneAndSaysWhatTheCapCut(t *testing.T) {
	open := []api.ProjectItem{
		queuedIn(sellProject, "s1", 11, 0),
		queuedIn(readingBacklog, "r2", 22, 1),
		queuedIn(readingBacklog, "r1", 21, 0),
	}

	run := runProjectsNext(t, open, nil, "-n", "1")

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

// The JSON is the overview's project_items section, so a consumer reads one
// shape from either command, with the totals the cap cut from.
func TestProjectsNext_JSONIsTheProjectWithItsCappedItemsAndCarriesNoNote(t *testing.T) {
	open := []api.ProjectItem{queuedIn(readingBacklog, "r1", 21, 0), queuedIn(readingBacklog, "r2", 22, 1)}

	run := runProjectsNext(t, open, nil, "-n", "1", "--json")

	var section projectItemSection
	if err := json.Unmarshal([]byte(run.stdout), &section); err != nil {
		t.Fatalf("stdout is not the project section: %v\n%s", err, run.stdout)
	}
	if section.Project == nil || section.Project.ID != "reading" {
		t.Errorf("--json project = %v, want the focus project", section.Project)
	}
	if len(section.Next) != 1 || section.Next[0].ID != "r1" || section.NextTotal != 2 {
		t.Errorf("--json next = %s of %d, want r1 of 2", itemIDs(section.Next), section.NextTotal)
	}
	if run.stderr != "" {
		t.Errorf("stderr = %q, want silence under --json", run.stderr)
	}
}

func TestProjectsNext_ABlockedFocusProjectListsWhatBlocksItInsteadOfMovingOn(t *testing.T) {
	stuck := queuedIn(readingBacklog, "r1", 21, 0)
	open := []api.ProjectItem{stuck, queuedIn(sellProject, "s1", 11, 0)}

	run := runProjectsNext(t, open, []api.ProjectItem{stuck})

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
