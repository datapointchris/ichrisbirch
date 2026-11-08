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
		if r.URL.Path == "/api/v1/project-items/blocked" {
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

// The JSON is the focus project with its capped items and the totals the cap
// cut from.
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

var activeProject = api.Project{ID: "live", Name: "Live", Status: api.ProjectStatusActive}

func TestFocusQueue_ExcludesWhatCannotBeTakenNow(t *testing.T) {
	shelved := api.Project{ID: "shelf", Name: "Shelf", Status: api.ProjectStatusSomeday}
	finished := api.Project{ID: "finished", Name: "Finished", Status: api.ProjectStatusCompleted}
	in := []api.Project{activeProject}

	all := []api.ProjectItem{
		{ID: "new", Title: "Newest", CreatedAt: fixedNow, Projects: in},
		{ID: "old", Title: "Oldest", CreatedAt: fixedNow.AddDate(0, 0, -10), Projects: in},
		{ID: "done", Title: "Completed", Completed: true, CreatedAt: fixedNow.AddDate(0, 0, -20), Projects: in},
		{ID: "archived", Title: "Archived", Archived: true, CreatedAt: fixedNow.AddDate(0, 0, -30), Projects: in},
		{ID: "blocked", Title: "Blocked", CreatedAt: fixedNow.AddDate(0, 0, -40), Projects: in},
		{ID: "shelved", Title: "Shelved", CreatedAt: fixedNow.AddDate(0, 0, -50), Projects: []api.Project{shelved}},
		{ID: "finished", Title: "Finished", CreatedAt: fixedNow.AddDate(0, 0, -60), Projects: []api.Project{finished}},
	}
	blocked := []api.ProjectItem{{ID: "blocked"}}

	focus := focusQueue(all, blocked, "")

	if len(focus.Next) != 2 {
		t.Fatalf("next = %s, want the two actionable items", itemIDs(focus.Next))
	}
	// Neither carries a position, so age is the whole order.
	if focus.Next[0].ID != "old" || focus.Next[1].ID != "new" {
		t.Errorf("next order = %s,%s — want oldest first", focus.Next[0].ID, focus.Next[1].ID)
	}
	if got := itemIDs(focus.Blocked); strings.Join(got, ",") != "blocked" {
		t.Errorf("blocked = %s, want the one item waiting on a dependency", got)
	}
}

// Projects are worked one at a time, so the second project's front item, older
// than anything in the first, stays off the queue entirely.
func TestFocusQueue_WorksTheHighestRankedProjectAlone(t *testing.T) {
	first := api.Project{ID: "first", Status: api.ProjectStatusActive, Position: 1, CreatedAt: fixedNow}
	second := api.Project{ID: "second", Status: api.ProjectStatusActive, Position: 2, CreatedAt: fixedNow.AddDate(0, 0, -100)}

	all := []api.ProjectItem{
		{
			ID: "second-front", CreatedAt: fixedNow.AddDate(0, 0, -90), Projects: []api.Project{second},
			Memberships: []api.ProjectItemMembership{{ProjectID: "second", Position: 0}},
		},
		{
			ID: "first-back", CreatedAt: fixedNow.AddDate(0, 0, -20), Projects: []api.Project{first},
			Memberships: []api.ProjectItemMembership{{ProjectID: "first", Position: 1}},
		},
		{
			ID: "first-front", CreatedAt: fixedNow, Projects: []api.Project{first},
			Memberships: []api.ProjectItemMembership{{ProjectID: "first", Position: 0}},
		},
	}

	focus := focusQueue(all, nil, "")

	if focus.Project == nil || focus.Project.ID != "first" {
		t.Fatalf("focus project = %+v, want first, the lower position", focus.Project)
	}
	want := []string{"first-front", "first-back"}
	if got := itemIDs(focus.Next); strings.Join(got, ",") != strings.Join(want, ",") {
		t.Errorf("next = %s, want %s and nothing from second", got, want)
	}
}

func TestFocusQueue_AnItemIsQueuedByItsPlaceInItsHighestRankedProject(t *testing.T) {
	first := api.Project{ID: "first", Status: api.ProjectStatusActive, Position: 1}
	second := api.Project{ID: "second", Status: api.ProjectStatusActive, Position: 2}

	all := []api.ProjectItem{
		{
			ID: "shared", CreatedAt: fixedNow.AddDate(0, 0, -10), Projects: []api.Project{second, first},
			Memberships: []api.ProjectItemMembership{
				{ProjectID: "second", Position: 0},
				{ProjectID: "first", Position: 3},
			},
		},
		{
			ID: "first-only", CreatedAt: fixedNow, Projects: []api.Project{first},
			Memberships: []api.ProjectItemMembership{{ProjectID: "first", Position: 2}},
		},
	}

	focus := focusQueue(all, nil, "")

	// shared is queued under first, where it sits behind first-only. Its place at
	// the front of second does not carry across.
	if got := itemIDs(focus.Next); strings.Join(got, ",") != "first-only,shared" {
		t.Errorf("next = %s, want first-only then shared", got)
	}
}

// A project that is not active keeps its memberships and its position 0, which
// sorts first, so ranking by it would make it the focus with nothing to work on.
func TestFocusQueue_AProjectThatIsNotActiveDoesNotRankAnItem(t *testing.T) {
	for _, status := range []string{api.ProjectStatusSomeday, api.ProjectStatusCompleted, api.ProjectStatusDropped} {
		inactive := api.Project{ID: "inactive", Status: status, Position: 0}
		first := api.Project{ID: "first", Status: api.ProjectStatusActive, Position: 1}
		later := api.Project{ID: "later", Status: api.ProjectStatusActive, Position: 2}

		all := []api.ProjectItem{
			{ID: "also-inactive", CreatedAt: fixedNow.AddDate(0, 0, -10), Projects: []api.Project{inactive, later}},
			{ID: "first-only", CreatedAt: fixedNow, Projects: []api.Project{first}},
		}

		focus := focusQueue(all, nil, "")

		if focus.Project == nil || focus.Project.ID != "first" {
			t.Fatalf("%s: focus project = %+v, want first", status, focus.Project)
		}
		if got := itemIDs(focus.Next); strings.Join(got, ",") != "first-only" {
			t.Errorf("%s: next = %s, want first-only; also-inactive is queued under later", status, got)
		}
	}
}

// Handing the focus to the next project would switch work without anyone
// deciding to, so a stuck project holds the queue until it is moved.
func TestFocusQueue_ABlockedFocusProjectKeepsTheFocus(t *testing.T) {
	first := api.Project{ID: "first", Name: "First", Status: api.ProjectStatusActive, Position: 1}
	second := api.Project{ID: "second", Name: "Second", Status: api.ProjectStatusActive, Position: 2}

	all := []api.ProjectItem{
		{ID: "waits", CreatedAt: fixedNow, Projects: []api.Project{first}},
		{ID: "free", CreatedAt: fixedNow, Projects: []api.Project{second}},
	}
	blocked := []api.ProjectItem{{ID: "waits"}}

	focus := focusQueue(all, blocked, "")

	if focus.Project == nil || focus.Project.ID != "first" {
		t.Fatalf("focus project = %+v, want first, though all of it is blocked", focus.Project)
	}
	if len(focus.Next) != 0 {
		t.Errorf("next = %s, want nothing: second's item must not take the queue", itemIDs(focus.Next))
	}
	if got := itemIDs(focus.Blocked); strings.Join(got, ",") != "waits" {
		t.Errorf("blocked = %s, want waits", got)
	}
}

func TestFocusQueue_NoActiveProjectIsNoFocus(t *testing.T) {
	shelved := api.Project{ID: "shelf", Status: api.ProjectStatusSomeday}
	all := []api.ProjectItem{{ID: "later", Projects: []api.Project{shelved}}}

	focus := focusQueue(all, nil, "")

	if focus.Project != nil || len(focus.Next) != 0 || len(focus.Blocked) != 0 {
		t.Errorf("focus = %+v, want no project and no items", focus)
	}
}

func TestFocusQueue_AMultiProjectItemIsQueuedOnce(t *testing.T) {
	selling := api.Project{ID: "selling", Name: "Sell Unused Shite", Status: api.ProjectStatusActive, CreatedAt: fixedNow.AddDate(0, 0, -100)}
	linux := api.Project{ID: "linux", Name: "Linux-first", Status: api.ProjectStatusActive, CreatedAt: fixedNow.AddDate(0, 0, -50)}

	all := []api.ProjectItem{
		{ID: "mac-mini", CreatedAt: fixedNow, Projects: []api.Project{linux, selling}},
		{ID: "monitors", CreatedAt: fixedNow.AddDate(0, 0, -1), Projects: []api.Project{selling}},
	}

	focus := focusQueue(all, nil, "")

	if len(focus.Next) != 2 {
		t.Fatalf("next = %s, want each item once however many projects it is in", itemIDs(focus.Next))
	}
	// mac-mini belongs to both, so it is queued under selling — the older, and
	// therefore higher-ranked, of its two projects — behind the older item there.
	if focus.Next[0].ID != "monitors" || focus.Next[1].ID != "mac-mini" {
		t.Errorf("next = %s, want monitors then mac-mini", itemIDs(focus.Next))
	}
}

func itemIDs(items []api.ProjectItem) []string {
	ids := make([]string, 0, len(items))
	for _, item := range items {
		ids = append(ids, item.ID)
	}
	return ids
}
