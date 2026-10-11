package cli

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"reflect"
	"slices"
	"strings"
	"testing"
	"time"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
)

// fixedNow is the reference clock for every composition test: a mid-afternoon
// local time, so same-day boundary cases are unambiguous.
var fixedNow = time.Date(2026, 7, 24, 15, 0, 0, 0, time.Local)

// An event's Date is the wall clock at the venue, so a fixture builds the string a
// server would send and states the zone that resolves it.
func eventWallClock(t time.Time) string { return t.Format(api.WallClockLayout) }

func TestBuildOverview_ComposesSections(t *testing.T) {
	data := overviewData{
		Tasks: []api.Task{
			{ID: 1, Name: "Renew passport", Category: "chore"},
			{ID: 2, Name: "Call dentist", Category: "chore"},
			{ID: 3, Name: "Fix garage door", Category: "home"},
		},
		HabitsDay: api.HabitsDay{
			Date:         "2026-07-24",
			Timezone:     "America/New_York",
			Due:          []api.Habit{{ID: 1, Name: "Stretch", CategoryID: 2}},
			Completed:    []api.HabitCompleted{{ID: 9, HabitID: habitID(2), Name: "Read", CategoryID: 2, CompleteDate: "2026-07-24"}},
			CurrentTotal: 2,
		},
		OwnedBooks: []api.Book{
			{ID: 1, Title: "Difficult Conversations", Author: "Stone", Progress: "reading"},
			{ID: 2, Title: "Music Theory", Author: "Hein", Progress: "unread"},
			{ID: 3, Title: "Finished One", Author: "X", Progress: "read"},
		},
		Items: []api.ProjectItem{
			{ID: "a", Title: "Older item", CreatedAt: fixedNow.AddDate(0, 0, -5), Projects: []api.Project{activeProject}},
			{ID: "b", Title: "Newer item", CreatedAt: fixedNow.AddDate(0, 0, -1), Projects: []api.Project{activeProject}},
			{ID: "c", Title: "Done item", Completed: true, CreatedAt: fixedNow, Projects: []api.Project{activeProject}},
		},
		BlockedItems: []api.ProjectItem{{ID: "b", Title: "Newer item"}},
		Countdowns:   []api.Countdown{{ID: 1, Name: "Lease renewal", DueDate: "2026-08-05"}},
		Events:       []api.Event{{ID: 1, Name: "Hike", Date: eventWallClock(fixedNow.AddDate(0, 0, 3)), Timezone: "Local"}},
		UnreadArticles: []api.Article{
			{ID: 5, Title: "The one being read"},
			{ID: 6, Title: "Still queued"},
		},
		CurrentArticle: &api.Article{ID: 5, Title: "The one being read"},
		Failures: []sectionFailure{
			{Section: sectionBooks, Label: "books", Err: &api.APIError{StatusCode: 500, Status: "500 Internal Server Error"}},
		},
	}

	report := buildOverview(data, fixedNow, 2)

	if report.SchemaVersion != overviewSchemaVersion {
		t.Errorf("schema version = %d, want %d", report.SchemaVersion, overviewSchemaVersion)
	}
	if len(report.Tasks.Items) != 2 {
		t.Errorf("tasks capped to %d, want 2", len(report.Tasks.Items))
	}
	if report.Tasks.Total != 3 {
		t.Errorf("tasks total = %d, want the pre-cap 3", report.Tasks.Total)
	}
	if len(report.Habits.DueToday) != 1 || report.Habits.DueToday[0].Name != "Stretch" {
		t.Errorf("due habits = %+v, want only Stretch", report.Habits.DueToday)
	}
	if report.Habits.CurrentTotal != 2 {
		t.Errorf("current habit total = %d, want 2", report.Habits.CurrentTotal)
	}
	if len(report.Books.Reading) != 1 || report.Books.Reading[0].Title != "Difficult Conversations" {
		t.Errorf("books being read = %+v", report.Books.Reading)
	}
	if report.Books.NextUpTotal != 1 {
		t.Errorf("next up total = %d, want 1", report.Books.NextUpTotal)
	}
	if report.Articles.Current == nil || report.Articles.Current.ID != 5 {
		t.Errorf("current article = %+v, want id 5", report.Articles.Current)
	}
	if report.Articles.UnreadTotal != 1 || report.Articles.Unread[0].ID != 6 {
		t.Errorf("unread articles = %+v — the current one must not also be queued", report.Articles.Unread)
	}
	if len(report.ProjectItems.Next) != 1 || report.ProjectItems.Next[0].ID != "a" {
		t.Errorf("next items = %+v, want only the unblocked, incomplete one", report.ProjectItems.Next)
	}
	if report.ProjectItems.BlockedTotal != 1 {
		t.Errorf("blocked total = %d, want 1", report.ProjectItems.BlockedTotal)
	}
	if report.Countdowns.Total != 1 || report.Events.Total != 1 {
		t.Errorf("countdowns/events totals = %d/%d, want 1/1", report.Countdowns.Total, report.Events.Total)
	}
	if len(report.Warnings) != 1 || report.Warnings[0].Section != sectionBooks {
		t.Fatalf("warnings = %+v, want one keyed to books", report.Warnings)
	}
	if !strings.Contains(report.Warnings[0].Message, "books") {
		t.Errorf("warning message = %q, want the failing call labeled", report.Warnings[0].Message)
	}
}

func TestBuildOverview_EmptyDataIsNotAFailure(t *testing.T) {
	report := buildOverview(overviewData{}, fixedNow, defaultOverviewLimit)

	if report.Tasks.Total != 0 || len(report.Warnings) != 0 {
		t.Errorf("empty data produced %d tasks and %d warnings", report.Tasks.Total, len(report.Warnings))
	}
	if report.Articles.Current != nil {
		t.Errorf("current article = %+v, want nil", report.Articles.Current)
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

func TestBooksByProgress_PreservesServerOrder(t *testing.T) {
	books := []api.Book{
		{ID: 1, Title: "First unread", Progress: "unread"},
		{ID: 2, Title: "Reading", Progress: "reading"},
		{ID: 3, Title: "Second unread", Progress: "unread"},
	}

	unread := booksByProgress(books, "unread")

	if len(unread) != 2 || unread[0].ID != 1 || unread[1].ID != 3 {
		t.Errorf("unread = %+v, want ids 1 then 3 in server (priority) order", unread)
	}
}

// An expired claim sorts as ready, not in progress. A decision in triage
// counts as triage.
func TestSortIssueQueue_KeepsDecisionsOutOfTheAgentQueue(t *testing.T) {
	queue := sortIssueQueue([]api.Issue{
		{Number: 1, Type: "bug", Status: api.IssueStatusOpen, IsReady: true},
		{Number: 2, Type: api.IssueTypeDecision, Status: api.IssueStatusOpen, IsReady: true},
		{Number: 3, Type: "task", Status: api.IssueStatusInProgress, IsReady: true},
		{Number: 4, Type: "task", Status: api.IssueStatusInProgress},
		{Number: 5, Type: api.IssueTypeDecision, Status: api.IssueStatusTriage},
		{Number: 6, Type: "chore", Status: api.IssueStatusOpen, IsBlocked: true},
	})
	numbers := func(issues []api.Issue) []int {
		out := []int{}
		for _, issue := range issues {
			out = append(out, issue.Number)
		}
		return out
	}
	if got := numbers(queue.ready); !slices.Equal(got, []int{1, 3}) {
		t.Errorf("ready = %v, want 1 then the expired claim 3", got)
	}
	if got := numbers(queue.inProgress); !slices.Equal(got, []int{4}) {
		t.Errorf("in progress = %v, want the live claim 4", got)
	}
	if got := numbers(queue.decisions); !slices.Equal(got, []int{2}) {
		t.Errorf("decisions = %v, want 2 alone", got)
	}
	if queue.triage != 1 {
		t.Errorf("triage = %d, want the triaged decision counted there", queue.triage)
	}
}

func TestUpcomingCountdownsDropThePast(t *testing.T) {
	countdowns := upcomingCountdowns([]api.Countdown{
		{ID: 1, Name: "Past", DueDate: "2026-07-01"},
		{ID: 2, Name: "Today", DueDate: "2026-07-24"},
		{ID: 3, Name: "Future", DueDate: "2026-09-01"},
	}, fixedNow)
	if len(countdowns) != 2 || countdowns[0].ID != 2 {
		t.Errorf("countdowns = %+v, want today and future, soonest first", countdowns)
	}
}

func TestCapItems(t *testing.T) {
	items := []int{1, 2, 3, 4}

	if got := capItems(items, 2); len(got) != 2 {
		t.Errorf("capItems(4, 2) = %v", got)
	}
	// Zero is a row count, so it caps to nothing. Every row is what an absent
	// --limit asks for, and the flag's default is what reaches here instead.
	if got := capItems(items, 0); len(got) != 0 {
		t.Errorf("capItems(4, 0) = %v, want nothing", got)
	}
	if got := capItems(items, 10); len(got) != 4 {
		t.Errorf("capItems(4, 10) = %v", got)
	}
	// Why an empty answer is allocated is on capItems itself.
	for name, got := range map[string][]int{
		"nil in":       capItems([]int(nil), 20),
		"empty in":     capItems([]int{}, 20),
		"negative cap": capItems(items, -1),
		"cap to zero":  capItems(items, 0),
	} {
		if got == nil {
			t.Errorf("capItems(%s) = nil, want an allocated slice so it marshals as []", name)
		}
	}
}

// Reflection rather than a written list of fields, so a section added later is
// covered by existing.
func TestBuildOverview_EmptyDataLeavesNoSectionAsNull(t *testing.T) {
	report := buildOverview(overviewData{}, fixedNow, defaultOverviewLimit)

	assertNoNilSlices(t, reflect.ValueOf(report), "report")

	encoded, err := json.Marshal(report)
	if err != nil {
		t.Fatalf("marshaling: %v", err)
	}
	// A nullable scalar is a different thing from an empty collection, so the
	// two that are genuinely absent stay null and only the arrays are asserted.
	for _, want := range []string{`"due_today":[]`, `"completed_today":[]`, `"items":[]`, `"unread":[]`, `"warnings":[]`} {
		if !bytes.Contains(encoded, []byte(want)) {
			t.Errorf("missing %s in:\n%s", want, encoded)
		}
	}
}

func assertNoNilSlices(t *testing.T, v reflect.Value, path string) {
	t.Helper()
	switch v.Kind() {
	case reflect.Struct:
		for i := range v.NumField() {
			assertNoNilSlices(t, v.Field(i), path+"."+v.Type().Field(i).Name)
		}
	case reflect.Pointer:
		if !v.IsNil() {
			assertNoNilSlices(t, v.Elem(), path)
		}
	case reflect.Slice:
		if v.IsNil() {
			t.Errorf("%s is nil, so it marshals as null where a caller expects []", path)
		}
	}
}

// overviewServer serves every overview endpoint with an empty list, except the
// paths in failures, which return the given status.
func overviewServer(t *testing.T, failures map[string]int) *httptest.Server {
	t.Helper()
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if status, failed := failures[r.URL.Path]; failed {
			w.WriteHeader(status)
			_, _ = w.Write([]byte(`{"error":"Internal Server Error","message":"boom"}`))
			return
		}
		w.Header().Set("Content-Type", "application/json")
		if r.URL.Path == "/api/v1/articles/current" {
			_, _ = w.Write([]byte(`null`))
			return
		}
		if r.URL.Path == "/api/v1/habits/day" {
			_, _ = w.Write([]byte(`{"date":"2026-07-24","timezone":"UTC","due":[],"completed":[],"current_total":0}`))
			return
		}
		_, _ = w.Write([]byte(`[]`))
	}))
	t.Cleanup(srv.Close)
	return srv
}

func TestFetchOverview_PartialFailureIsIsolated(t *testing.T) {
	srv := overviewServer(t, map[string]int{"/api/v1/books": http.StatusInternalServerError})
	client := api.New(srv.URL, srv.Client())

	data := fetchOverview(context.Background(), client)

	if len(data.Failures) != 1 {
		t.Fatalf("failures = %+v, want only the books call", data.Failures)
	}
	if data.Failures[0].Section != sectionBooks {
		t.Errorf("failure section = %q, want %q", data.Failures[0].Section, sectionBooks)
	}
	if err := systemicOverviewFailure(data.Failures, len(overviewFetches())); err != nil {
		t.Errorf("systemic failure = %v, want a partial snapshot to survive", err)
	}
}

func TestSystemicOverviewFailure(t *testing.T) {
	unauthorized := []sectionFailure{
		{Section: sectionTasks, Label: "tasks", Err: &api.APIError{StatusCode: http.StatusUnauthorized, Status: "401 Unauthorized"}},
	}
	if err := systemicOverviewFailure(unauthorized, 9); err == nil {
		t.Error("a 401 in any section must fail the whole command")
	}

	// What a service client gets on every section outside its scope.
	forbidden := []sectionFailure{
		{Section: sectionTasks, Label: "tasks", Err: &api.APIError{StatusCode: http.StatusForbidden, Status: "403 Forbidden"}},
	}
	if err := systemicOverviewFailure(forbidden, 9); err == nil {
		t.Error("a 403 in any section must fail the whole command")
	}

	serverErrors := []sectionFailure{
		{Section: sectionTasks, Label: "tasks", Err: &api.APIError{StatusCode: 500, Status: "500"}},
		{Section: sectionEvents, Label: "events", Err: &api.APIError{StatusCode: 500, Status: "500"}},
	}
	if err := systemicOverviewFailure(serverErrors, 2); err == nil {
		t.Error("every section failing must fail the whole command")
	}
	if err := systemicOverviewFailure(serverErrors, 9); err != nil {
		t.Errorf("two of nine sections failing must stay partial, got %v", err)
	}
}

func TestPrintOverview(t *testing.T) {
	report := buildOverview(overviewData{
		Tasks: []api.Task{{ID: 1, Name: "Renew passport", Category: "chore"}},
		HabitsDay: api.HabitsDay{
			Due:          []api.Habit{{ID: 1, Name: "Stretch", CategoryID: 2}},
			Completed:    []api.HabitCompleted{{ID: 9, HabitID: habitID(2), Name: "Read", CategoryID: 2, CompleteDate: "2026-07-24"}},
			CurrentTotal: 2,
		},
		Failures: []sectionFailure{
			{Section: sectionBooks, Label: "books", Err: &api.APIError{StatusCode: 500, Status: "500 Internal Server Error"}},
		},
	}, fixedNow, defaultOverviewLimit)

	var out, errOut bytes.Buffer
	printOverview(&out, &errOut, report)
	text := out.String()

	for _, want := range []string{"Tasks (1 open)", "Renew passport", "due: Stretch"} {
		if !strings.Contains(text, want) {
			t.Errorf("printed overview missing %q:\n%s", want, text)
		}
	}
	if !strings.Contains(errOut.String(), "warning: books: books") {
		t.Errorf("degraded section not warned on stderr:\n%s", errOut.String())
	}
	if strings.Contains(text, "books: books") {
		t.Errorf("a warning reached stdout, which corrupts the snapshot stream:\n%s", text)
	}
}

func TestPrintOverview_EmptyStates(t *testing.T) {
	var out, errOut bytes.Buffer
	printOverview(&out, &errOut, buildOverview(overviewData{}, fixedNow, defaultOverviewLimit))
	text := out.String()

	for _, want := range []string{"Tasks (0 open)", "(none)", "(all done)"} {
		if !strings.Contains(text, want) {
			t.Errorf("empty overview missing %q:\n%s", want, text)
		}
	}
}

func TestArticlesBehindCurrent_DropsTheOneBeingRead(t *testing.T) {
	unread := []api.Article{{ID: 1, Title: "First"}, {ID: 2, Title: "Current"}, {ID: 3, Title: "Third"}}

	queued := articlesBehindCurrent(unread, &api.Article{ID: 2, Title: "Current"})

	if len(queued) != 2 || queued[0].ID != 1 || queued[1].ID != 3 {
		t.Errorf("queued = %+v — the current article must not also be counted as waiting", queued)
	}
	if all := articlesBehindCurrent(unread, nil); len(all) != 3 {
		t.Errorf("with no current article the whole queue stands, got %+v", all)
	}
}

func TestArticlesBehindCurrent_PutsTheOldestSavedFirst(t *testing.T) {
	unread := []api.Article{
		{ID: 1, Title: "A recent save", SaveDate: fixedNow.AddDate(0, 0, -2)},
		{ID: 2, Title: "Zz saved years ago", SaveDate: fixedNow.AddDate(-2, 0, 0)},
		{ID: 3, Title: "Mid", SaveDate: fixedNow.AddDate(0, -3, 0)},
	}

	queued := articlesBehindCurrent(unread, nil)

	if ids := []int{queued[0].ID, queued[1].ID, queued[2].ID}; !slices.Equal(ids, []int{2, 3, 1}) {
		t.Errorf("queue order = %v, want the oldest save first whatever its title", ids)
	}
}

func readAt(daysAgo int) *time.Time {
	when := fixedNow.AddDate(0, 0, -daysAgo)
	return &when
}

func TestArticleReadActivity_CountsTheWindowAndKeepsTheLatest(t *testing.T) {
	read := []api.Article{
		{ID: 1, LastReadDate: readAt(10)},
		{ID: 2, LastReadDate: readAt(2)},
		{ID: 3, LastReadDate: readAt(60)},
	}

	last, inWindow := articleReadActivity(read, fixedNow)

	if inWindow != 2 {
		t.Errorf("read in window = %d, want 2 — the 60-day-old read is outside it", inWindow)
	}
	if last == nil || !last.Equal(*readAt(2)) {
		t.Errorf("last read = %v, want the most recent of the three", last)
	}
}

func TestArticleReadActivity_AnArchivedRowWithNoReadDateIsNotReading(t *testing.T) {
	read := []api.Article{{ID: 1, IsArchived: true, LastReadDate: nil}}

	last, inWindow := articleReadActivity(read, fixedNow)

	if last != nil || inWindow != 0 {
		t.Errorf("last = %v, inWindow = %d — an archive with no read date is not evidence of reading", last, inWindow)
	}
}

func TestArticleReadActivity_NothingEverReadHasNoDate(t *testing.T) {
	last, inWindow := articleReadActivity(nil, fixedNow)

	if last != nil || inWindow != 0 {
		t.Errorf("last = %v, inWindow = %d — an untouched list must report no date", last, inWindow)
	}
}

func TestPrintOverview_ArticlesSayWhetherThePileIsMoving(t *testing.T) {
	report := buildOverview(overviewData{
		UnreadArticles: []api.Article{{ID: 6, Title: "A Queued Article"}},
		ReadArticles: []api.Article{
			{ID: 1, Title: "Read Recently", IsArchived: true, LastReadDate: readAt(3)},
			{ID: 2, Title: "Read Long Ago", IsArchived: true, LastReadDate: readAt(90)},
		},
	}, fixedNow, defaultOverviewLimit)

	if report.Articles.ReadLast30Days != 1 {
		t.Errorf("read_last_30_days = %d, want 1", report.Articles.ReadLast30Days)
	}

	var out, errOut bytes.Buffer
	printOverview(&out, &errOut, report)

	want := "Articles (1 unread, 1 read in 30d, last 2026-07-21)"
	if !strings.Contains(out.String(), want) {
		t.Errorf("printed overview missing %q:\n%s", want, out.String())
	}
}

func TestPrintOverview_AnUntouchedArticleListSaysOnlyItsCount(t *testing.T) {
	report := buildOverview(overviewData{
		UnreadArticles: []api.Article{{ID: 6, Title: "A Queued Article"}},
	}, fixedNow, defaultOverviewLimit)

	var out, errOut bytes.Buffer
	printOverview(&out, &errOut, report)

	if !strings.Contains(out.String(), "Articles (1 unread)") {
		t.Errorf("a list nobody has read must not claim 0 read:\n%s", out.String())
	}
}

// Every row is in one project, so the header names it once instead of each row.
func TestPrintProjectItemSection_NamesTheFocusProjectOnce(t *testing.T) {
	project := api.Project{Name: "Sell Unused Shite"}
	var out bytes.Buffer

	printProjectItemSection(&out, projectItemSection{
		Project:   &project,
		Next:      []api.ProjectItem{{Title: "Glove 80"}, {Title: "Monitors"}},
		NextTotal: 2,
	})

	got := out.String()
	if !strings.Contains(got, "Project items: Sell Unused Shite (2 next, 0 blocked)") {
		t.Errorf("header = %q, want the focus project named with its counts", got)
	}
	if strings.Count(got, "Sell Unused Shite") != 1 {
		t.Errorf("section = %q, want the project named once, in the header", got)
	}
}

func TestPrintProjectItemSection_NoFocusProjectIsNone(t *testing.T) {
	var out bytes.Buffer

	printProjectItemSection(&out, projectItemSection{})

	if !strings.Contains(out.String(), "(none)") {
		t.Errorf("section = %q, want (none) when no active project holds an open item", out.String())
	}
}

func TestPrintOverview_SeparatesBooksFromArticles(t *testing.T) {
	report := buildOverview(overviewData{
		OwnedBooks:     []api.Book{{ID: 1, Title: "A Book", Author: "Author", Progress: "reading"}},
		CurrentArticle: &api.Article{ID: 5, Title: "An Article"},
		UnreadArticles: []api.Article{{ID: 5, Title: "An Article"}, {ID: 6, Title: "A Queued Article"}},
		Items: []api.ProjectItem{
			{ID: "a", Title: "Glove 80", Projects: []api.Project{{Name: "Sell Unused Shite", Status: api.ProjectStatusActive}}, CreatedAt: fixedNow},
		},
	}, fixedNow, defaultOverviewLimit)

	var out, errOut bytes.Buffer
	printOverview(&out, &errOut, report)
	text := out.String()

	for _, want := range []string{"Books (1 reading, 0 queued)", "A Book", "Articles (1 unread)", "An Article", "Sell Unused Shite"} {
		if !strings.Contains(text, want) {
			t.Errorf("printed overview missing %q:\n%s", want, text)
		}
	}
}

func TestTruncateTitle_CollapsesScrapedWhitespace(t *testing.T) {
	if got := truncateTitle("\n\tRAG on structured data with PostgreSQL\n"); got != "RAG on structured data with PostgreSQL" {
		t.Errorf("truncateTitle = %q — a wrapped title breaks tabwriter alignment", got)
	}
	if got := truncateTitle("  spaced   out  "); got != "spaced out" {
		t.Errorf("truncateTitle = %q, want inner runs collapsed too", got)
	}
}

func habitID(v int) *int { return &v }
