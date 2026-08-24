package api

import (
	"context"
	"fmt"
	"net/http"
	"time"
)

// Event mirrors the events JSON. Date is a full datetime (RFC3339). URL and Notes
// are nullable.
type Event struct {
	ID        int       `json:"id"`
	Name      string    `json:"name"`
	Date      time.Time `json:"date"`
	Venue     string    `json:"venue"`
	URL       *string   `json:"url"`
	Cost      float64   `json:"cost"`
	Attending bool      `json:"attending"`
	Notes     *string   `json:"notes"`
}

// EventCreateInput is the body for creating an event. Name, Date, Venue, Cost,
// and Attending are required by the API. Date is sent as a string so the server's
// flexible (pendulum) parser handles any timezone-less input.
type EventCreateInput struct {
	Name      string  `json:"name"`
	Date      string  `json:"date"`
	Venue     string  `json:"venue"`
	Cost      float64 `json:"cost"`
	Attending bool    `json:"attending"`
	URL       *string `json:"url,omitempty"`
	Notes     *string `json:"notes,omitempty"`
}

// EventUpdateInput is a partial update (PATCH /events/{id}/). Date is a string
// pointer for the same parsing reason as create.
type EventUpdateInput struct {
	Name      *string  `json:"name,omitempty"`
	Date      *string  `json:"date,omitempty"`
	Venue     *string  `json:"venue,omitempty"`
	Cost      *float64 `json:"cost,omitempty"`
	Attending *bool    `json:"attending,omitempty"`
	URL       *string  `json:"url,omitempty"`
	Notes     *string  `json:"notes,omitempty"`
}

// ListEvents returns events ordered by date (GET /events/).
func (c *Client) ListEvents(ctx context.Context) ([]Event, error) {
	var events []Event
	if err := c.get(ctx, "/events/", &events); err != nil {
		return nil, err
	}
	return events, nil
}

// GetEvent returns a single event (GET /events/{id}/). Missing is 404.
func (c *Client) GetEvent(ctx context.Context, id int) (Event, error) {
	var event Event
	if err := c.get(ctx, fmt.Sprintf("/events/%d/", id), &event); err != nil {
		return Event{}, err
	}
	return event, nil
}

// CreateEvent creates an event (POST /events/).
func (c *Client) CreateEvent(ctx context.Context, in EventCreateInput) (Event, error) {
	var event Event
	if err := c.send(ctx, http.MethodPost, "/events/", in, &event); err != nil {
		return Event{}, err
	}
	return event, nil
}

// UpdateEvent applies a partial update (PATCH /events/{id}/).
func (c *Client) UpdateEvent(ctx context.Context, id int, in EventUpdateInput) (Event, error) {
	var event Event
	if err := c.send(ctx, http.MethodPatch, fmt.Sprintf("/events/%d/", id), in, &event); err != nil {
		return Event{}, err
	}
	return event, nil
}

// DeleteEvent removes an event (DELETE /events/{id}/ → 204).
func (c *Client) DeleteEvent(ctx context.Context, id int) error {
	return c.send(ctx, http.MethodDelete, fmt.Sprintf("/events/%d/", id), nil, nil)
}

// AttendEvent marks an event as attending (PATCH /events/{id}/attend/).
func (c *Client) AttendEvent(ctx context.Context, id int) (Event, error) {
	var event Event
	if err := c.send(ctx, http.MethodPatch, fmt.Sprintf("/events/%d/attend/", id), nil, &event); err != nil {
		return Event{}, err
	}
	return event, nil
}
