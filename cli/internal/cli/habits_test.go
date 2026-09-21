package cli

import (
	"errors"
	"slices"
	"strings"
	"testing"
	"time"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
)

// The zone is pinned rather than taken from the runner. At 21:30 in New York it
// is already the next day in UTC, and a runner in UTC would not see the two
// calendars disagree.
func newYork(t *testing.T) *time.Location {
	t.Helper()
	loc, err := time.LoadLocation("America/New_York")
	if err != nil {
		t.Fatalf("loading zone: %v", err)
	}
	return loc
}

func evening(t *testing.T) time.Time {
	return time.Date(2026, 8, 23, 21, 30, 0, 0, newYork(t))
}

func TestHabitCompleteDate_NoFlagIsTodayOnTheLocalCalendar(t *testing.T) {
	got, err := habitCompleteDate("", evening(t))
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got != "2026-08-23" {
		t.Errorf("want 2026-08-23, the New York day rather than the UTC one, got %s", got)
	}
}

func TestHabitCompleteDate_TodayIsAccepted(t *testing.T) {
	got, err := habitCompleteDate("2026-08-23", evening(t))
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got != "2026-08-23" {
		t.Errorf("want 2026-08-23, got %s", got)
	}
}

func TestHabitCompleteDate_AnEarlierDayIsThatDay(t *testing.T) {
	got, err := habitCompleteDate("2026-08-21", evening(t))
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got != "2026-08-21" {
		t.Errorf("want 2026-08-21, got %s", got)
	}
}

func TestHabitCompleteDate_ADayThatDoesNotExistIsAFormatRefusal(t *testing.T) {
	_, err := habitCompleteDate("2026-02-31", evening(t))
	if !errors.Is(err, errDateFormat) {
		t.Fatalf("want errDateFormat, got %v", err)
	}
}

func TestHabitCompleteDate_TomorrowIsRefused(t *testing.T) {
	_, err := habitCompleteDate("2026-08-24", evening(t))
	if !errors.Is(err, errDateInFuture) {
		t.Fatalf("want errDateInFuture, got %v", err)
	}
	if errors.Is(err, errDateFormat) {
		t.Error("a future date is not a format error")
	}
}

func TestHabitCompleteDate_AMalformedDateIsAFormatRefusal(t *testing.T) {
	_, err := habitCompleteDate("21-08-2026", evening(t))
	if !errors.Is(err, errDateFormat) {
		t.Fatalf("want errDateFormat, got %v", err)
	}
	if errors.Is(err, errDateInFuture) {
		t.Error("a malformed date is not a future-date error")
	}
}

func TestHabitCompleteDate_ARefusalIsAUsageError(t *testing.T) {
	// Exit code 2 rather than 1 depends on this, and Unwrap is what lets both
	// the sentinel check above and this one see the same error.
	var usage usageError
	_, err := habitCompleteDate("2026-08-24", evening(t))
	if !errors.As(err, &usage) {
		t.Fatalf("want a usageError, got %T", err)
	}
}

// The server sends both halves in habit-id order. Merging them on that id is
// what keeps a finished habit in its row rather than moving it to a trailing
// block, which would reshuffle the board every time one is ticked off.
func TestHabitsDayRows_InterleavesDoneByID(t *testing.T) {
	board := api.HabitsDay{
		Due: []api.Habit{
			{ID: 3, Name: "Floss", CategoryID: 2, Category: api.HabitCategory{ID: 2, Name: "Health"}},
			{ID: 4, Name: "Read", CategoryID: 5, Category: api.HabitCategory{ID: 5, Name: "Mind"}},
		},
		Completed: []api.HabitCompleted{
			{ID: 10, HabitID: intPtr(1), Name: "Brush", CategoryID: 2, Category: api.HabitCategory{ID: 2, Name: "Health"}},
		},
		CurrentTotal: 3,
	}

	rows := habitsDayRows(board)

	var got []int
	for _, row := range rows {
		got = append(got, row.ID)
	}
	if want := []int{1, 3, 4}; !slices.Equal(got, want) {
		t.Errorf("row order = %v, want %v", got, want)
	}
	if !rows[0].Done || rows[1].Done {
		t.Errorf("rows = %+v — habit 1 is the completed one", rows)
	}
}

// An orphan completion has no habit id to place it by, so it goes last rather
// than ahead of habit id 1.
func TestHabitsDayRows_AnOrphanCompletionSortsLast(t *testing.T) {
	board := api.HabitsDay{
		Due: []api.Habit{
			{ID: 1, Name: "Floss", CategoryID: 2, Category: api.HabitCategory{ID: 2, Name: "Health"}},
		},
		Completed: []api.HabitCompleted{
			{ID: 10, Name: "Deleted habit", CategoryID: 2, Category: api.HabitCategory{ID: 2, Name: "Health"}},
		},
		CurrentTotal: 1,
	}

	rows := habitsDayRows(board)

	if len(rows) != 2 || rows[1].Name != "Deleted habit" {
		t.Fatalf("rows = %+v, want the orphan last", rows)
	}
	if rows[1].ID != 0 {
		t.Errorf("id = %d, want 0 — the completion's own id is not a habit id", rows[1].ID)
	}
}

func TestPrintHabitsDay_ShowsTheCountTheZoneAndEveryRow(t *testing.T) {
	board := api.HabitsDay{
		Date:     "2026-09-20",
		Timezone: "America/New_York",
		Due: []api.Habit{
			{ID: 3, Name: "Floss", CategoryID: 2, Category: api.HabitCategory{ID: 2, Name: "Health"}},
		},
		Completed: []api.HabitCompleted{
			{ID: 10, HabitID: intPtr(1), Name: "Brush", CategoryID: 2, Category: api.HabitCategory{ID: 2, Name: "Health"}},
		},
		CurrentTotal: 2,
	}

	var out strings.Builder
	printHabitsDay(&out, board)
	got := out.String()

	for _, want := range []string{"1 of 2 done today", "America/New_York", "Brush", "Floss", "icb habits complete <id>"} {
		if !strings.Contains(got, want) {
			t.Errorf("output missing %q:\n%s", want, got)
		}
	}
}

// The zone decides which completions land on the board, so a day read in UTC
// because the machine could not name its zone has to say so rather than look
// like any other morning.
func TestPrintHabitsDay_NamesTheZoneTheDayWasReadIn(t *testing.T) {
	var out strings.Builder
	printHabitsDay(&out, api.HabitsDay{Date: "2026-09-20", Timezone: "UTC", CurrentTotal: 0})

	if !strings.Contains(out.String(), "UTC") {
		t.Errorf("output does not name the zone:\n%s", out.String())
	}
}

// Nothing due means nothing to type, so the command hint is left off rather than
// pointing at a board with no outstanding row on it.
func TestPrintHabitsDay_DropsTheHintWhenEverythingIsDone(t *testing.T) {
	board := api.HabitsDay{
		Timezone: "UTC",
		Completed: []api.HabitCompleted{
			{ID: 10, HabitID: intPtr(1), Name: "Brush", CategoryID: 2, Category: api.HabitCategory{ID: 2, Name: "Health"}},
		},
		CurrentTotal: 1,
	}

	var out strings.Builder
	printHabitsDay(&out, board)

	if strings.Contains(out.String(), "icb habits complete") {
		t.Errorf("output offers a completion with nothing due:\n%s", out.String())
	}
}
