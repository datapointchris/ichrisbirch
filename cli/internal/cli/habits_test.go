package cli

import (
	"encoding/json"
	"errors"
	"slices"
	"strings"
	"testing"
	"time"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
)

// The zone is pinned rather than taken from the runner. The noon rule is about a
// wall clock, and a runner in UTC has no offset shift for the rule to survive.
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

func TestHabitCompleteDate_NoFlagIsTheMomentItRan(t *testing.T) {
	now := evening(t)
	got, err := habitCompleteDate("", now)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !got.Equal(now) {
		t.Errorf("want %v, got %v", now, got)
	}
}

func TestHabitCompleteDate_TodayKeepsTheMomentRatherThanNoon(t *testing.T) {
	now := evening(t)
	got, err := habitCompleteDate("2026-08-23", now)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !got.Equal(now) {
		t.Errorf("want the current moment %v, got %v", now, got)
	}
}

func TestHabitCompleteDate_AnEarlierDayLandsAtLocalNoon(t *testing.T) {
	got, err := habitCompleteDate("2026-08-21", evening(t))
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	want := time.Date(2026, 8, 21, 12, 0, 0, 0, newYork(t))
	if !got.Equal(want) {
		t.Errorf("want %v, got %v", want, got)
	}
}

// Adding twelve hours to local midnight lands at 13:00 on the spring-forward day
// and 11:00 on the fall-back day, because a duration is absolute and the offset
// moves underneath it. Noon has to be constructed, not reached.
func TestHabitCompleteDate_NoonIsNoonOnDaysTheOffsetShifts(t *testing.T) {
	loc := newYork(t)
	now := time.Date(2026, 12, 1, 9, 0, 0, 0, loc)

	for _, day := range []string{"2026-03-08", "2026-11-01"} {
		got, err := habitCompleteDate(day, now)
		if err != nil {
			t.Fatalf("%s: unexpected error: %v", day, err)
		}
		if got.Hour() != 12 {
			t.Errorf("%s: want hour 12, got %d (%v)", day, got.Hour(), got)
		}
		if got.Format("2006-01-02") != day {
			t.Errorf("%s: want the same calendar day, got %v", day, got)
		}
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

// The board is ordered by id, which never changes, so a habit sits in the same
// row all day. The API answers in its own order, so the ordering is imposed here
// rather than relied on.
func TestBuildHabitsTodayBoard_OrdersByID(t *testing.T) {
	current := []api.Habit{
		{ID: 8, Name: "Yoga", CategoryID: 2, Category: api.HabitCategory{ID: 2, Name: "Health"}},
		{ID: 2, Name: "Read", CategoryID: 5, Category: api.HabitCategory{ID: 5, Name: "Mind"}},
		{ID: 5, Name: "Floss", CategoryID: 2, Category: api.HabitCategory{ID: 2, Name: "Health"}},
	}

	board := buildHabitsTodayBoard(current, nil, fixedNow)

	var got []int
	for _, habit := range board.DueToday {
		got = append(got, habit.ID)
	}
	if want := []int{2, 5, 8}; !slices.Equal(got, want) {
		t.Errorf("due order = %v, want %v", got, want)
	}
}

// The header reads "N of M done today", and M is every current habit rather than
// the ones still outstanding. Counting only the due ones would print "0 of 0" on
// the day everything is finished.
func TestBuildHabitsTodayBoard_CurrentTotalCountsEveryTrackedHabit(t *testing.T) {
	current := []api.Habit{
		{ID: 1, Name: "Yoga", CategoryID: 2, Category: api.HabitCategory{ID: 2, Name: "Health"}},
		{ID: 2, Name: "Floss", CategoryID: 2, Category: api.HabitCategory{ID: 2, Name: "Health"}},
	}
	completed := []api.HabitCompleted{
		{ID: 10, HabitID: intPtr(1), Name: "Yoga", CategoryID: 2, Category: api.HabitCategory{ID: 2, Name: "Health"}, CompleteDate: habitAt(7, 0)},
	}

	board := buildHabitsTodayBoard(current, completed, fixedNow)

	if board.CurrentTotal != 2 {
		t.Errorf("current total = %d, want 2", board.CurrentTotal)
	}
	if len(board.CompletedToday) != 1 || len(board.DueToday) != 1 {
		t.Errorf("board = %+v, want one done and one due", board)
	}
}

// A done habit keeps its row. Moving the finished ones into a trailing block
// would reshuffle the board every time one is ticked off, which is the thing the
// ordering exists to prevent.
func TestHabitsTodayRows_InterleavesDoneByID(t *testing.T) {
	section := habitSection{
		DueToday: []api.Habit{
			{ID: 3, Name: "Floss", CategoryID: 2, Category: api.HabitCategory{ID: 2, Name: "Health"}},
			{ID: 4, Name: "Read", CategoryID: 5, Category: api.HabitCategory{ID: 5, Name: "Mind"}},
		},
		CompletedToday: []api.HabitCompleted{
			{ID: 10, HabitID: intPtr(1), Name: "Brush", CategoryID: 2, Category: api.HabitCategory{ID: 2, Name: "Health"}},
		},
		CurrentTotal: 3,
	}

	rows := habitsTodayRows(section)

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
func TestHabitsTodayRows_AnOrphanCompletionSortsLast(t *testing.T) {
	section := habitSection{
		DueToday: []api.Habit{
			{ID: 1, Name: "Floss", CategoryID: 2, Category: api.HabitCategory{ID: 2, Name: "Health"}},
		},
		CompletedToday: []api.HabitCompleted{
			{ID: 10, Name: "Deleted habit", CategoryID: 2, Category: api.HabitCategory{ID: 2, Name: "Health"}},
		},
		CurrentTotal: 1,
	}

	rows := habitsTodayRows(section)

	if len(rows) != 2 || rows[1].Name != "Deleted habit" {
		t.Errorf("rows = %+v, want the orphan last", rows)
	}
}

// A completion whose habit has been deleted still belongs on the board, and it is
// the one row with no id to print. Printing the completion's own id there would
// hand back a number `icb habits complete` rejects.
func TestHabitsTodayRows_AnOrphanCompletionCarriesNoHabitID(t *testing.T) {
	section := habitSection{
		CompletedToday: []api.HabitCompleted{
			{ID: 10, Name: "Old habit", CategoryID: 2, Category: api.HabitCategory{ID: 2, Name: "Health"}},
		},
	}

	rows := habitsTodayRows(section)

	if len(rows) != 1 {
		t.Fatalf("rows = %+v, want the orphan completion", rows)
	}
	if rows[0].ID != 0 {
		t.Errorf("id = %d, want 0 — the completion's own id is not a habit id", rows[0].ID)
	}
}

// Both halves marshal as [] when empty. A reader that branches on the array would
// otherwise have to handle null as well, on exactly the day everything is done.
func TestBuildHabitsTodayBoard_EmptyHalvesMarshalAsArrays(t *testing.T) {
	board := buildHabitsTodayBoard(nil, nil, fixedNow)

	encoded, err := json.Marshal(board)
	if err != nil {
		t.Fatalf("marshaling: %v", err)
	}
	if strings.Contains(string(encoded), "null") {
		t.Errorf("json = %s, want [] for both halves", encoded)
	}
}

func TestPrintHabitsToday_ShowsTheCountAndEveryRow(t *testing.T) {
	section := habitSection{
		DueToday: []api.Habit{
			{ID: 3, Name: "Floss", CategoryID: 2, Category: api.HabitCategory{ID: 2, Name: "Health"}},
		},
		CompletedToday: []api.HabitCompleted{
			{ID: 10, HabitID: intPtr(1), Name: "Brush", CategoryID: 2, Category: api.HabitCategory{ID: 2, Name: "Health"}},
		},
		CurrentTotal: 2,
	}

	var out strings.Builder
	printHabitsToday(&out, section)
	got := out.String()

	for _, want := range []string{"Habits (1 of 2 done today)", "Brush", "Floss", "icb habits complete <id>"} {
		if !strings.Contains(got, want) {
			t.Errorf("output missing %q:\n%s", want, got)
		}
	}
}

// Nothing due means nothing to type, so the command hint is left off rather than
// pointing at a board with no outstanding row on it.
func TestPrintHabitsToday_DropsTheHintWhenEverythingIsDone(t *testing.T) {
	section := habitSection{
		CompletedToday: []api.HabitCompleted{
			{ID: 10, HabitID: intPtr(1), Name: "Brush", CategoryID: 2, Category: api.HabitCategory{ID: 2, Name: "Health"}},
		},
		CurrentTotal: 1,
	}

	var out strings.Builder
	printHabitsToday(&out, section)

	if strings.Contains(out.String(), "icb habits complete") {
		t.Errorf("output offers a completion with nothing due:\n%s", out.String())
	}
}
