package api

import "net/url"

// DateBounds narrows a list read to rows whose date column falls in a range. One
// type across every resource because --start and --end mean the same thing on
// each: both bounds are inclusive, either narrows on its own, and the server
// owns the WHERE.
//
// A resource's own filter struct would give four spellings of one idea, which is
// the drift the shared flag names exist to prevent. Empty strings add nothing to
// the query, so a caller with no bounds sends an unchanged request.
type DateBounds struct {
	Start string
	End   string
}

// apply writes the bounds into params under the query names the API takes.
func (b DateBounds) apply(params url.Values) {
	if b.Start != "" {
		params.Set("start_date", b.Start)
	}
	if b.End != "" {
		params.Set("end_date", b.End)
	}
}
