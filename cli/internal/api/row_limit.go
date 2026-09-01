package api

import (
	"net/url"
	"strconv"
)

// applyLimit writes a row cap into params, or writes nothing when there is no
// cap to apply. One helper across every list read because --limit means the
// same thing on each: at most this many rows, server-side.
//
// A nil limit and a limit of zero or less are the same answer — every row — and
// neither is sent. Not sending it is what makes `--limit 0` mean "all" against
// any version of the API: an API that reads a bare `limit=0` as `LIMIT 0` would
// answer with nothing, which is the opposite of what the flag was asked for.
func applyLimit(params url.Values, limit *int) {
	if limit == nil || *limit <= 0 {
		return
	}
	params.Set("limit", strconv.Itoa(*limit))
}
