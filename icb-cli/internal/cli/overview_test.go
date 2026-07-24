package cli

import (
	"bytes"
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"ichrisbirch/cli/internal/api"
)

// fixedNow is the reference clock for every composition test: a mid-afternoon
// local time, so same-day boundary cases are unambiguous.
var fixedNow = time.Date(2026, 7, 24, 15, 0, 0, 0, time.Local)

func habitAt(hour int, minute int) time.Time {
	return time.Date(2026, 7, 24, hour, minute, 0, 0, time.Local)
}

func TestBuildOverview_ComposesSections(t *testing.T) {
	data := overviewData{
		Tasks: []api.Task{
			{ID: 1, Name: "Renew passport", Category: "chore", Priority: 1},
			{ID: 2, Name: "Call dentist", Category: "chore", Priority: 2},
			{ID: 3, Name: "Fix garage door", Category: "home", Priority: 3},
		},
		CurrentHabits: []api.Habit{
			{ID: 1, Name: "Stretch", CategoryID: 2},
			{ID: 2, Name: "Read", CategoryID: 2},
		},
		CompletedHabits: []api.HabitCompleted{
			{ID: 9, Name: "Read", CategoryID: 2, CompleteDate: habitAt(8, 0)},
		},
		OwnedBooks: []api.Book{
			{ID: 1, Title: "Difficult Conversations", Author: "Stone", Progress: "reading"},
			{ID: 2, Title: "Music Theory", Author: "Hein", Progress: "unread"},
			{ID: 3, Title: "Finished One", Author: "X", Progress: "read"},
		},
		Items: []api.ProjectItem{
			{ID: "a", Title: "Older item", CreatedAt: fixedNow.AddDate(0, 0, -5)},
			{ID: "b", Title: "Newer item", CreatedAt: fixedNow.AddDate(0, 0, -1)},
			{ID: "c", Title: "Done item", Completed: true, CreatedAt: fixedNow},
		},
		BlockedItems: []api.ProjectItem{{ID: "b", Title: "Newer item"}},
		Countdowns:   []api.Countdown{{ID: 1, Name: "Lease renewal", DueDate: "2026-08-05"}},
		Events:       []api.Event{{ID: 1, Name: "Hike", Date: fixedNow.AddDate(0, 0, 3)}},
		Failures: []sectionFailure{
			{Section: sectionReading, Label: "books", Err: &api.APIError{StatusCode: 500, Status: "500 Internal Server Error"}},
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
	if len(report.Reading.Reading) != 1 || report.Reading.Reading[0].Title != "Difficult Conversations" {
		t.Errorf("reading = %+v", report.Reading.Reading)
	}
	if report.Reading.NextUpTotal != 1 {
		t.Errorf("next up total = %d, want 1", report.Reading.NextUpTotal)
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
	if len(report.Warnings) != 1 || report.Warnings[0].Section != sectionReading {
		t.Fatalf("warnings = %+v, want one keyed to reading", report.Warnings)
	}
	if !strings.Contains(report.Warnings[0].Message, "books") {
		t.Errorf("warning message = %q, want the failing call labelled", report.Warnings[0].Message)
	}
}

func TestBuildOverview_EmptyDataIsNotAFailure(t *testing.T) {
	report := buildOverview(overviewData{}, fixedNow, defaultOverviewLimit)

	if report.Tasks.Total != 0 || len(report.Warnings) != 0 {
		t.Errorf("empty data produced %d tasks and %d warnings", report.Tasks.Total, len(report.Warnings))
	}
	if report.Reading.CurrentArticle != nil {
		t.Errorf("current article = %+v, want nil", report.Reading.CurrentArticle)
	}
}

func TestSplitHabitsByCompletion(t *testing.T) {
	current := []api.Habit{
		{ID: 1, Name: "Stretch", CategoryID: 2},
		{ID: 2, Name: "Read", CategoryID: 2},
		{ID: 3, Name: "Read", CategoryID: 5},
	}
	completed := []api.HabitCompleted{
		{ID: 10, Name: "Read", CategoryID: 2, CompleteDate: habitAt(23, 30)},
		{ID: 11, Name: "Stretch", CategoryID: 2, CompleteDate: habitAt(9, 0).AddDate(0, 0, -1)},
	}

	due, doneToday := splitHabitsByCompletion(current, completed, fixedNow)

	if len(doneToday) != 1 || doneToday[0].ID != 10 {
		t.Errorf("done today = %+v, want only the 23:30 local completion", doneToday)
	}
	if len(due) != 2 {
		t.Fatalf("due = %+v, want Stretch (done yesterday) and Read in the other category", due)
	}
	if due[0].Name != "Stretch" || due[1].CategoryID != 5 {
		t.Errorf("due = %+v — category must be part of the match key", due)
	}
}

func TestSplitHabitsByCompletion_RenameOrphansTodaysCompletion(t *testing.T) {
	current := []api.Habit{{ID: 1, Name: "Stretch daily", CategoryID: 2}}
	completed := []api.HabitCompleted{{ID: 10, Name: "Stretch", CategoryID: 2, CompleteDate: habitAt(8, 0)}}

	due, doneToday := splitHabitsByCompletion(current, completed, fixedNow)

	if len(due) != 1 {
		t.Errorf("due = %+v — a renamed habit cannot match its completion, so it reads as due", due)
	}
	if len(doneToday) != 1 {
		t.Errorf("done today = %+v, want the completion still reported", doneToday)
	}
}

func TestLocalDayWindow_SpansTheLocalDayWithSlack(t *testing.T) {
	start, end := localDayWindow(fixedNow)

	if start != "2026-07-23" {
		t.Errorf("start = %q, want the day before", start)
	}
	if end != "2026-07-26" {
		t.Errorf("end = %q, want two days after — a zero-width window matches nothing", end)
	}
}

func TestNextProjectItems_ExcludesAndOrders(t *testing.T) {
	all := []api.ProjectItem{
		{ID: "new", Title: "Newest", CreatedAt: fixedNow},
		{ID: "old", Title: "Oldest", CreatedAt: fixedNow.AddDate(0, 0, -10)},
		{ID: "done", Title: "Completed", Completed: true, CreatedAt: fixedNow.AddDate(0, 0, -20)},
		{ID: "archived", Title: "Archived", Archived: true, CreatedAt: fixedNow.AddDate(0, 0, -30)},
		{ID: "blocked", Title: "Blocked", CreatedAt: fixedNow.AddDate(0, 0, -40)},
	}
	blocked := []api.ProjectItem{{ID: "blocked"}}

	next := nextProjectItems(all, blocked)

	if len(next) != 2 {
		t.Fatalf("next = %+v, want the two actionable items", next)
	}
	if next[0].ID != "old" || next[1].ID != "new" {
		t.Errorf("next order = %s,%s — want oldest first", next[0].ID, next[1].ID)
	}
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

func TestUpcomingFiltersDropThePast(t *testing.T) {
	countdowns := upcomingCountdowns([]api.Countdown{
		{ID: 1, Name: "Past", DueDate: "2026-07-01"},
		{ID: 2, Name: "Today", DueDate: "2026-07-24"},
		{ID: 3, Name: "Future", DueDate: "2026-09-01"},
	}, fixedNow)
	if len(countdowns) != 2 || countdowns[0].ID != 2 {
		t.Errorf("countdowns = %+v, want today and future, soonest first", countdowns)
	}

	events := upcomingEvents([]api.Event{
		{ID: 1, Name: "Yesterday", Date: fixedNow.AddDate(0, 0, -1)},
		{ID: 2, Name: "This morning", Date: habitAt(6, 0)},
		{ID: 3, Name: "Next week", Date: fixedNow.AddDate(0, 0, 7)},
	}, fixedNow)
	if len(events) != 2 || events[0].ID != 2 {
		t.Errorf("events = %+v — earlier today must survive, yesterday must not", events)
	}
}

func TestCapItems(t *testing.T) {
	items := []int{1, 2, 3, 4}

	if got := capItems(items, 2); len(got) != 2 {
		t.Errorf("capItems(4, 2) = %v", got)
	}
	if got := capItems(items, 0); len(got) != 4 {
		t.Errorf("capItems(4, 0) = %v, want no cap", got)
	}
	if got := capItems(items, 10); len(got) != 4 {
		t.Errorf("capItems(4, 10) = %v", got)
	}
}

// overviewServer serves every overview endpoint with an empty list, except the
// paths in failures, which return the given status.
func overviewServer(t *testing.T, failures map[string]int) *httptest.Server {
	t.Helper()
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if status, failed := failures[r.URL.Path]; failed {
			w.WriteHeader(status)
			_, _ = w.Write([]byte(`{"detail":"boom"}`))
			return
		}
		w.Header().Set("Content-Type", "application/json")
		if r.URL.Path == "/articles/current/" {
			_, _ = w.Write([]byte(`null`))
			return
		}
		_, _ = w.Write([]byte(`[]`))
	}))
	t.Cleanup(srv.Close)
	return srv
}

func TestFetchOverview_PartialFailureIsIsolated(t *testing.T) {
	srv := overviewServer(t, map[string]int{"/books/": http.StatusInternalServerError})
	client := api.New(srv.URL, srv.Client())

	data := fetchOverview(context.Background(), client)

	if len(data.Failures) != 1 {
		t.Fatalf("failures = %+v, want only the books call", data.Failures)
	}
	if data.Failures[0].Section != sectionReading {
		t.Errorf("failure section = %q, want %q", data.Failures[0].Section, sectionReading)
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
		Tasks:           []api.Task{{ID: 1, Name: "Renew passport", Category: "chore", Priority: 1}},
		CurrentHabits:   []api.Habit{{ID: 1, Name: "Stretch", CategoryID: 2}},
		CompletedHabits: []api.HabitCompleted{{ID: 9, Name: "Read", CategoryID: 2, CompleteDate: habitAt(8, 0)}},
		Failures: []sectionFailure{
			{Section: sectionReading, Label: "books", Err: &api.APIError{StatusCode: 500, Status: "500 Internal Server Error"}},
		},
	}, fixedNow, defaultOverviewLimit)

	var out bytes.Buffer
	printOverview(&out, report)
	text := out.String()

	for _, want := range []string{"Tasks (1 open)", "Renew passport", "due: Stretch", "Warnings", "reading: books"} {
		if !strings.Contains(text, want) {
			t.Errorf("printed overview missing %q:\n%s", want, text)
		}
	}
}

func TestPrintOverview_EmptyStates(t *testing.T) {
	var out bytes.Buffer
	printOverview(&out, buildOverview(overviewData{}, fixedNow, defaultOverviewLimit))
	text := out.String()

	for _, want := range []string{"Tasks (0 open)", "(none)", "(all done)"} {
		if !strings.Contains(text, want) {
			t.Errorf("empty overview missing %q:\n%s", want, text)
		}
	}
}
