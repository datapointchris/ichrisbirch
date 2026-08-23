package cli

import (
	"strings"
	"testing"
	"time"
)

func evening() time.Time {
	return time.Date(2026, 8, 23, 21, 30, 0, 0, time.Local)
}

func TestHabitCompleteDate_NoFlagIsTheMomentItRan(t *testing.T) {
	now := evening()
	got, err := habitCompleteDate("", now)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !got.Equal(now) {
		t.Errorf("want %v, got %v", now, got)
	}
}

func TestHabitCompleteDate_TodayKeepsTheMomentRatherThanNoon(t *testing.T) {
	now := evening()
	got, err := habitCompleteDate("2026-08-23", now)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !got.Equal(now) {
		t.Errorf("want the current moment %v, got %v", now, got)
	}
}

func TestHabitCompleteDate_AnEarlierDayLandsAtLocalNoon(t *testing.T) {
	got, err := habitCompleteDate("2026-08-21", evening())
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	want := time.Date(2026, 8, 21, 12, 0, 0, 0, time.Local)
	if !got.Equal(want) {
		t.Errorf("want %v, got %v", want, got)
	}
}

func TestHabitCompleteDate_NoonHoldsAcrossADaylightSavingBoundary(t *testing.T) {
	// A day stamped at midnight could cross into the adjacent day when rendered
	// at another offset. Noon is the margin that keeps the completion on its own day.
	got, err := habitCompleteDate("2026-03-08", evening())
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got.Day() != 8 || got.Month() != time.March {
		t.Errorf("want 2026-03-08, got %v", got)
	}
	if got.UTC().Day() != 8 {
		t.Errorf("want the same day in UTC, got %v", got.UTC())
	}
}

func TestHabitCompleteDate_TomorrowIsRefused(t *testing.T) {
	_, err := habitCompleteDate("2026-08-24", evening())
	if err == nil {
		t.Fatal("want an error for a future date, got nil")
	}
	if !strings.Contains(err.Error(), "future") {
		t.Errorf("error should say the date is in the future, got %q", err)
	}
}

func TestHabitCompleteDate_AMalformedDateNamesTheExpectedShape(t *testing.T) {
	_, err := habitCompleteDate("21-08-2026", evening())
	if err == nil {
		t.Fatal("want an error for a malformed date, got nil")
	}
	if !strings.Contains(err.Error(), "YYYY-MM-DD") {
		t.Errorf("error should name the expected format, got %q", err)
	}
}
