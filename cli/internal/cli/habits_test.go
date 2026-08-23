package cli

import (
	"errors"
	"testing"
	"time"
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
