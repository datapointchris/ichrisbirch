package api

import (
	"context"
	"fmt"
	"net/http"
)

// Countdown mirrors the countdowns JSON. DueDate is a date-only field, kept as a
// string ("2006-01-02") because Go's time.Time JSON unmarshalling requires
// RFC3339 and would reject a bare date.
type Countdown struct {
	ID      int     `json:"id"`
	Name    string  `json:"name"`
	Notes   *string `json:"notes"`
	DueDate string  `json:"due_date"`
}

// CountdownCreateInput is the body for creating a countdown. Name and DueDate
// (YYYY-MM-DD) are required.
type CountdownCreateInput struct {
	Name    string  `json:"name"`
	Notes   *string `json:"notes,omitempty"`
	DueDate string  `json:"due_date"`
}

// CountdownUpdateInput is a partial update (PATCH /countdowns/{id}/).
type CountdownUpdateInput struct {
	Name    *string `json:"name,omitempty"`
	Notes   *string `json:"notes,omitempty"`
	DueDate *string `json:"due_date,omitempty"`
}

// ListCountdowns returns countdowns ordered by due date (GET /countdowns/).
func (c *Client) ListCountdowns(ctx context.Context) ([]Countdown, error) {
	var countdowns []Countdown
	if err := c.get(ctx, "/countdowns/", &countdowns); err != nil {
		return nil, err
	}
	return countdowns, nil
}

// GetCountdown returns a single countdown (GET /countdowns/{id}/). Missing is 404.
func (c *Client) GetCountdown(ctx context.Context, id int) (Countdown, error) {
	var countdown Countdown
	if err := c.get(ctx, fmt.Sprintf("/countdowns/%d/", id), &countdown); err != nil {
		return Countdown{}, err
	}
	return countdown, nil
}

// CreateCountdown creates a countdown (POST /countdowns/).
func (c *Client) CreateCountdown(ctx context.Context, in CountdownCreateInput) (Countdown, error) {
	var countdown Countdown
	if err := c.send(ctx, http.MethodPost, "/countdowns/", in, &countdown); err != nil {
		return Countdown{}, err
	}
	return countdown, nil
}

// UpdateCountdown applies a partial update (PATCH /countdowns/{id}/).
func (c *Client) UpdateCountdown(ctx context.Context, id int, in CountdownUpdateInput) (Countdown, error) {
	var countdown Countdown
	if err := c.send(ctx, http.MethodPatch, fmt.Sprintf("/countdowns/%d/", id), in, &countdown); err != nil {
		return Countdown{}, err
	}
	return countdown, nil
}

// DeleteCountdown removes a countdown (DELETE /countdowns/{id}/ → 204).
func (c *Client) DeleteCountdown(ctx context.Context, id int) error {
	return c.send(ctx, http.MethodDelete, fmt.Sprintf("/countdowns/%d/", id), nil, nil)
}
