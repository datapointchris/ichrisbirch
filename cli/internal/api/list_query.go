package api

import (
	"net/url"
	"strconv"
)

// applyLimit writes a row cap into params, or writes nothing when there is no
// cap to apply. One helper across every list read because --limit means the
// same thing on each: at most this many rows, server-side.
//
// A nil limit is the absence of a cap and is not sent, which is what asks for
// every row. A limit of zero is a row count the caller can mean, so it is sent
// as `limit=0` and the API answers with nothing. Folding the two together
// answers a caller computing its own bound with the whole collection.
func applyLimit(params url.Values, limit *int) {
	if limit == nil {
		return
	}
	params.Set("limit", strconv.Itoa(*limit))
}

// OnOrAfter is the inclusive lower bound of a list read's date range, an ISO
// 8601 date or datetime. Empty narrows nothing.
//
// The two bounds and the zone are separate types because they sit side by
// side in each signature that takes them. As plain strings, a start and end
// passed in each other's place compile, and the API returns an empty list.
type OnOrAfter string

// OnOrBefore is the inclusive upper bound, read the same way as OnOrAfter.
type OnOrBefore string

// DayZone is the IANA zone a bound with no offset is read in, for a column
// that stores instants. A task finished at 21:00 in New York is on the next
// day in UTC. Empty leaves the server to read it in the user's preference.
type DayZone string

// applyDateBounds writes a date range into params. Either bound narrows on its
// own, and an empty one is not sent. The zone goes only with a bound, since it
// means nothing on its own.
func applyDateBounds(params url.Values, start OnOrAfter, end OnOrBefore, zone DayZone) {
	if start != "" {
		params.Set("start_date", string(start))
	}
	if end != "" {
		params.Set("end_date", string(end))
	}
	if zone != "" && (start != "" || end != "") {
		params.Set("timezone", string(zone))
	}
}
