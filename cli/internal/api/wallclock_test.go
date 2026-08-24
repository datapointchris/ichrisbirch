package api

import (
	"encoding/json"
	"testing"
	"time"
)

// time.Time's JSON decode requires RFC3339, so a bare day or an offsetless wall
// clock takes the whole response down — one dated row fails the entire list call.
// These pin the shapes the API actually sends onto the fields that receive them.
func TestBookDecodes_ACalendarDay(t *testing.T) {
	var book Book
	if err := json.Unmarshal([]byte(`{"id":1,"purchase_date":"2026-08-20","read_finish_date":null}`), &book); err != nil {
		t.Fatalf("decoding a bare day: %v", err)
	}
	if book.PurchaseDate == nil || *book.PurchaseDate != "2026-08-20" {
		t.Errorf("purchase_date = %v, want the day verbatim", book.PurchaseDate)
	}
	if book.ReadFinishDate != nil {
		t.Errorf("read_finish_date = %v, want nil", book.ReadFinishDate)
	}
}

func TestEventDecodes_AWallClockAndItsZone(t *testing.T) {
	var event Event
	body := `{"id":1,"name":"Show","date":"2026-09-28T19:00:00","timezone":"America/New_York","venue":"Hall","cost":0,"attending":true}`
	if err := json.Unmarshal([]byte(body), &event); err != nil {
		t.Fatalf("decoding an offsetless wall clock: %v", err)
	}
	if event.Date != "2026-09-28T19:00:00" || event.Timezone != "America/New_York" {
		t.Errorf("event = %+v", event)
	}
}

func TestEventInstant_ResolvesAgainstTheEventsOwnZone(t *testing.T) {
	tokyo := Event{Date: "2026-09-28T09:00:00", Timezone: "Asia/Tokyo"}
	newYork := Event{Date: "2026-09-28T08:00:00", Timezone: "America/New_York"}

	// 09:00 in Tokyo is thirteen hours before 08:00 in New York, and comparing the
	// readings says the opposite.
	if !EventInstant(tokyo).Before(EventInstant(newYork)) {
		t.Errorf("tokyo %v should precede new york %v", EventInstant(tokyo), EventInstant(newYork))
	}
	if tokyo.Date < newYork.Date {
		t.Error("guard: the string comparison is expected to disagree, which is why the resolver exists")
	}
}

func TestEventInstant_AMissingZoneReadsAsUTC(t *testing.T) {
	got := EventInstant(Event{Date: "2026-09-28T09:00:00"})
	want := time.Date(2026, 9, 28, 9, 0, 0, 0, time.UTC)
	if !got.Equal(want) {
		t.Errorf("got %v, want %v", got, want)
	}
}

func TestEventInstant_ARowThatWillNotParseIsZeroRatherThanAPanic(t *testing.T) {
	if !EventInstant(Event{Date: "not a date", Timezone: "UTC"}).IsZero() {
		t.Error("want the zero time for an unreadable row")
	}
}

func TestEventWhen_NamesTheZoneSoTheReadingIsUnambiguous(t *testing.T) {
	got := EventWhen(Event{Date: "2026-09-28T19:00:00", Timezone: "America/New_York"})
	if got != "2026-09-28 19:00 America/New_York" {
		t.Errorf("got %q", got)
	}
}
