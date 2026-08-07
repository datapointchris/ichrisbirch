package api

import (
	"context"
	"fmt"
	"net/http"
	"net/url"
	"strconv"
)

// Pattern mirrors the patterns JSON.
type Pattern struct {
	ID         int    `json:"id"`
	Message    string `json:"message"`
	RecordedAt string `json:"recorded_at"`
}

// PatternCreateInput is the body for creating a pattern. RecordedAt is optional
// — the API stamps now when it is omitted, which is what makes a capture one
// argument.
type PatternCreateInput struct {
	Message    string  `json:"message"`
	RecordedAt *string `json:"recorded_at,omitempty"`
}

// PatternUpdateInput is a partial update (PATCH /patterns/{id}/).
type PatternUpdateInput struct {
	Message    *string `json:"message,omitempty"`
	RecordedAt *string `json:"recorded_at,omitempty"`
}

// PatternListOptions filters the list. Zero values mean unfiltered.
type PatternListOptions struct {
	Search string
	Limit  int
}

// ListPatterns returns patterns newest first (GET /patterns/).
func (c *Client) ListPatterns(ctx context.Context, opts PatternListOptions) ([]Pattern, error) {
	query := url.Values{}
	if opts.Search != "" {
		query.Set("search", opts.Search)
	}
	if opts.Limit > 0 {
		query.Set("limit", strconv.Itoa(opts.Limit))
	}

	path := "/patterns/"
	if encoded := query.Encode(); encoded != "" {
		path += "?" + encoded
	}

	var patterns []Pattern
	if err := c.get(ctx, path, &patterns); err != nil {
		return nil, err
	}
	return patterns, nil
}

// GetPattern returns a single pattern (GET /patterns/{id}/). Missing is 404.
func (c *Client) GetPattern(ctx context.Context, id int) (Pattern, error) {
	var pattern Pattern
	if err := c.get(ctx, fmt.Sprintf("/patterns/%d/", id), &pattern); err != nil {
		return Pattern{}, err
	}
	return pattern, nil
}

// CreatePattern creates a pattern (POST /patterns/).
func (c *Client) CreatePattern(ctx context.Context, in PatternCreateInput) (Pattern, error) {
	var pattern Pattern
	if err := c.send(ctx, http.MethodPost, "/patterns/", in, &pattern); err != nil {
		return Pattern{}, err
	}
	return pattern, nil
}

// UpdatePattern applies a partial update (PATCH /patterns/{id}/).
func (c *Client) UpdatePattern(ctx context.Context, id int, in PatternUpdateInput) (Pattern, error) {
	var pattern Pattern
	if err := c.send(ctx, http.MethodPatch, fmt.Sprintf("/patterns/%d/", id), in, &pattern); err != nil {
		return Pattern{}, err
	}
	return pattern, nil
}

// DeletePattern removes a pattern (DELETE /patterns/{id}/ → 204).
func (c *Client) DeletePattern(ctx context.Context, id int) error {
	return c.send(ctx, http.MethodDelete, fmt.Sprintf("/patterns/%d/", id), nil, nil)
}
