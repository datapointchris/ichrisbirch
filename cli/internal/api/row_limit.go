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
