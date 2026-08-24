package api

import (
	"fmt"
	"time"
)

// WallClockLayout is the shape a naive venue-local datetime arrives in.
const WallClockLayout = "2006-01-02T15:04:05"

// EventInstant resolves an event's wall clock against its own zone, which is the
// only way to compare two events or an event against now. Date alone is a reading
// on a clock somewhere else: 09:00 in Tokyo is earlier than 08:00 in New York, and
// comparing the strings says the opposite.
//
// A date that will not parse, or an unknown zone, falls back to the wall clock read as UTC,
// so a bad row sorts somewhere plausible rather than taking the command down.
func EventInstant(e Event) time.Time {
	zone := e.Timezone
	if zone == "" {
		zone = "UTC"
	}
	loc, err := time.LoadLocation(zone)
	if err != nil {
		loc = time.UTC
	}
	t, err := time.ParseInLocation(WallClockLayout, e.Date, loc)
	if err != nil {
		// The API also emits a bare date for an all-day entry.
		if t, err = time.ParseInLocation("2006-01-02", e.Date, loc); err != nil {
			return time.Time{}
		}
	}
	return t
}

// EventWhen renders the reading as it would be read at the venue, naming the zone
// so a reader elsewhere knows which clock it is. Rendering it in the reader's own
// zone would move the number and say nothing about where the event is.
func EventWhen(e Event) string {
	t := EventInstant(e)
	if t.IsZero() {
		return e.Date
	}
	zone := e.Timezone
	if zone == "" {
		zone = "UTC"
	}
	return fmt.Sprintf("%s %s", t.Format("2006-01-02 15:04"), zone)
}
