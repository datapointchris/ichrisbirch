package api

import (
	"context"
	"fmt"
	"net/http"
	"net/url"
	"sort"
	"strconv"
)

// Strain mirrors the strains JSON — a catalog row for a marijuana strain.
// Nullable columns are pointers; the four array columns are NOT NULL DEFAULT
// '{}' server-side and so arrive as a list rather than null.
//
// LastTriedDate is a calendar day ("2006-01-02") and stays a string, because
// Go's time.Time JSON decode requires RFC3339 and rejects a bare date. A whole
// slice decodes in one call, so one dated row in the wrong type fails the
// entire command — the same reason Countdown.DueDate is a string.
type Strain struct {
	ID            int      `json:"id"`
	Name          string   `json:"name"`
	Breeder       *string  `json:"breeder"`
	Lineage       *string  `json:"lineage"`
	StrainType    *string  `json:"strain_type"`
	Status        string   `json:"status"`
	THCPercent    *float64 `json:"thc_percent"`
	CBDPercent    *float64 `json:"cbd_percent"`
	Rating        *int     `json:"rating"`
	Effects       []string `json:"effects"`
	Flavors       []string `json:"flavors"`
	Terpenes      []string `json:"terpenes"`
	Tags          []string `json:"tags"`
	Source        *string  `json:"source"`
	Notes         *string  `json:"notes"`
	Review        *string  `json:"review"`
	LastTriedDate *string  `json:"last_tried_date"`
	CreatedAt     string   `json:"created_at"`
	UpdatedAt     string   `json:"updated_at"`
}

// StrainCreateInput is the body for creating a strain (POST /strains/). Only
// Name is required; a strain written down off a menu board has nothing else.
// Status defaults to want_to_try server-side.
type StrainCreateInput struct {
	Name          string   `json:"name"`
	Breeder       *string  `json:"breeder,omitempty"`
	Lineage       *string  `json:"lineage,omitempty"`
	StrainType    *string  `json:"strain_type,omitempty"`
	Status        *string  `json:"status,omitempty"`
	THCPercent    *float64 `json:"thc_percent,omitempty"`
	CBDPercent    *float64 `json:"cbd_percent,omitempty"`
	Rating        *int     `json:"rating,omitempty"`
	Effects       []string `json:"effects,omitempty"`
	Flavors       []string `json:"flavors,omitempty"`
	Terpenes      []string `json:"terpenes,omitempty"`
	Tags          []string `json:"tags,omitempty"`
	Source        *string  `json:"source,omitempty"`
	Notes         *string  `json:"notes,omitempty"`
	Review        *string  `json:"review,omitempty"`
	LastTriedDate *string  `json:"last_tried_date,omitempty"`
}

// StrainUpdateInput is a partial update (PATCH /strains/{id}/): only changed
// fields are sent. Emptying a field is `--clear <field>`, which mergeClearNulls
// writes as an explicit null after this struct is marshaled — the same grammar
// `icb recipes edit` and `icb cooking-techniques edit` take.
type StrainUpdateInput struct {
	Name          *string  `json:"name,omitempty"`
	Breeder       *string  `json:"breeder,omitempty"`
	Lineage       *string  `json:"lineage,omitempty"`
	StrainType    *string  `json:"strain_type,omitempty"`
	Status        *string  `json:"status,omitempty"`
	THCPercent    *float64 `json:"thc_percent,omitempty"`
	CBDPercent    *float64 `json:"cbd_percent,omitempty"`
	Rating        *int     `json:"rating,omitempty"`
	Effects       []string `json:"effects,omitempty"`
	Flavors       []string `json:"flavors,omitempty"`
	Terpenes      []string `json:"terpenes,omitempty"`
	Tags          []string `json:"tags,omitempty"`
	Source        *string  `json:"source,omitempty"`
	Notes         *string  `json:"notes,omitempty"`
	Review        *string  `json:"review,omitempty"`
	LastTriedDate *string  `json:"last_tried_date,omitempty"`
}

// StrainFilter narrows a listing. An empty field is not sent, so the zero value
// lists everything. Effect, Flavor and Terpene each match one value inside an
// array column, which is why they are singular where the record's field is
// plural. Query is the search, which narrows alongside the filters rather than
// from a route of its own.
type StrainFilter struct {
	StrainType string
	Status     string
	Effect     string
	Flavor     string
	Terpene    string
	RatingMin  int
	Query      string
}

func (f StrainFilter) query() url.Values {
	params := url.Values{}
	for name, value := range map[string]string{
		"strain_type": f.StrainType,
		"status":      f.Status,
		"effect":      f.Effect,
		"flavor":      f.Flavor,
		"terpene":     f.Terpene,
		"q":           f.Query,
	} {
		if value != "" {
			params.Set(name, value)
		}
	}
	if f.RatingMin != 0 {
		params.Set("rating_min", strconv.Itoa(f.RatingMin))
	}
	return params
}

// Active names the filters carrying a value, for an empty result that would
// otherwise read as an empty catalog.
func (f StrainFilter) Active() []string {
	var active []string
	for _, pair := range [][2]string{
		{"--type", f.StrainType},
		{"--status", f.Status},
		{"--effect", f.Effect},
		{"--flavor", f.Flavor},
		{"--terpene", f.Terpene},
		{"--query", f.Query},
	} {
		if pair[1] != "" {
			active = append(active, fmt.Sprintf("%s %s", pair[0], pair[1]))
		}
	}
	if f.RatingMin != 0 {
		active = append(active, fmt.Sprintf("--rating-min %d", f.RatingMin))
	}
	sort.Strings(active)
	return active
}

// StrainVocabularyEntry is one value a vocabulary defines, with how many
// strains carry it. A count of zero is a value nothing uses yet, not a gap.
type StrainVocabularyEntry struct {
	Name  string `json:"name"`
	Count int    `json:"count"`
}

// StrainVocabulary is every value each vocabulary defines. Fetched rather than
// compiled in, so adding an effect is an INSERT on the server and not a release
// of this binary.
// Each list is keyed by the record field it constrains, so a 422 naming
// `strain_type` and the list of values it would have accepted are found under
// the same word.
type StrainVocabulary struct {
	StrainType []StrainVocabularyEntry `json:"strain_type"`
	Status     []StrainVocabularyEntry `json:"status"`
	Effects    []StrainVocabularyEntry `json:"effects"`
	Flavors    []StrainVocabularyEntry `json:"flavors"`
	Terpenes   []StrainVocabularyEntry `json:"terpenes"`
}

// VocabularyNames returns just the values of one vocabulary list, for a
// prompt's Choices and for the validator that checks a flag against the same
// set. One source for both means neither door accepts what the other refuses.
func VocabularyNames(entries []StrainVocabularyEntry) []string {
	names := make([]string, 0, len(entries))
	for _, entry := range entries {
		names = append(names, entry.Name)
	}
	return names
}

// ListStrains returns strains by name (GET /strains/), narrowed by filter. A
// nil limit fetches all; a non-nil limit caps the count, so it takes the first
// names of whatever the filters left.
func (c *Client) ListStrains(ctx context.Context, filter StrainFilter, limit *int) ([]Strain, error) {
	params := filter.query()
	applyLimit(params, limit)
	path := withQuery("/strains/", params)
	var strains []Strain
	if err := c.get(ctx, path, &strains); err != nil {
		return nil, err
	}
	return strains, nil
}

// SearchStrains returns strains matching q across name, breeder, lineage,
// notes and tags. It is ListStrains with the search filled in, because the
// search is a parameter on the collection rather than a route of its own —
// which is what lets it compose with the filters and the limit.
// Comma-separated terms preserve phrases.
func (c *Client) SearchStrains(ctx context.Context, q string, limit *int) ([]Strain, error) {
	return c.ListStrains(ctx, StrainFilter{Query: q}, limit)
}

// GetStrainVocabulary returns every defined value of every strain vocabulary
// (GET /strains/vocabulary/), whether or not a strain carries it.
func (c *Client) GetStrainVocabulary(ctx context.Context) (StrainVocabulary, error) {
	var vocabulary StrainVocabulary
	if err := c.get(ctx, "/strains/vocabulary/", &vocabulary); err != nil {
		return StrainVocabulary{}, err
	}
	return vocabulary, nil
}

// GetStrain returns a single strain (GET /strains/{id}/). Missing is 404.
func (c *Client) GetStrain(ctx context.Context, id int) (Strain, error) {
	var strain Strain
	if err := c.get(ctx, fmt.Sprintf("/strains/%d/", id), &strain); err != nil {
		return Strain{}, err
	}
	return strain, nil
}

// CreateStrain creates a strain (POST /strains/).
func (c *Client) CreateStrain(ctx context.Context, in StrainCreateInput) (Strain, error) {
	var strain Strain
	if err := c.send(ctx, http.MethodPost, "/strains/", in, &strain); err != nil {
		return Strain{}, err
	}
	return strain, nil
}

// UpdateStrain applies a partial update (PATCH /strains/{id}/). Each field in
// clear is sent as an explicit null, which the API reads as "empty this" — for
// an array column that means the empty list.
func (c *Client) UpdateStrain(ctx context.Context, id int, in StrainUpdateInput, clear []string) (Strain, error) {
	body, err := mergeClearNulls(in, clear)
	if err != nil {
		return Strain{}, err
	}
	var strain Strain
	if err := c.send(ctx, http.MethodPatch, fmt.Sprintf("/strains/%d/", id), body, &strain); err != nil {
		return Strain{}, err
	}
	return strain, nil
}

// DeleteStrain removes a strain (DELETE /strains/{id}/ → 204).
func (c *Client) DeleteStrain(ctx context.Context, id int) error {
	return c.send(ctx, http.MethodDelete, fmt.Sprintf("/strains/%d/", id), nil, nil)
}
