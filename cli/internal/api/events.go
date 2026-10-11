package api

import (
	"context"
	"fmt"
	"net/http"
	"net/url"
)

// Event mirrors the events JSON. URL and Notes are nullable.
type Event struct {
	ID   int    `json:"id"`
	Name string `json:"name"`
	// The wall clock at the venue ("2006-01-02T15:04:05"), with Timezone holding the
	// IANA name that resolves it. A string rather than a time.Time: the value carries
	// no offset, and Go's time.Time JSON decode requires RFC3339 and would reject it.
	Date      string  `json:"date"`
	Timezone  string  `json:"timezone"`
	Venue     string  `json:"venue"`
	URL       *string `json:"url"`
	Cost      float64 `json:"cost"`
	Attending bool    `json:"attending"`
	Notes     *string `json:"notes"`
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

// EventUpdateInput is a partial update (PATCH /events/{id}). Date is a string
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

// EventScope picks which side of today a list read returns.
type EventScope string

const (
	// EventsUpcoming is today onward, soonest first. It is the server's default.
	EventsUpcoming EventScope = "upcoming"
	// EventsPast is before today, most recent first.
	EventsPast EventScope = "past"
	// EventsAll is every event in date order.
	EventsAll EventScope = "all"
)

// EventScopes lists every scope, in the order help text names them.
var EventScopes = []EventScope{EventsUpcoming, EventsPast, EventsAll}

// ListEvents returns one scope of events (GET /events). Today is read in zone,
// or in the user's preference when zone is empty. A nil limit fetches the whole
// scope, and a limit takes from its front: the soonest upcoming, the latest past.
func (c *Client) ListEvents(ctx context.Context, when EventScope, zone DayZone, limit *int) ([]Event, error) {
	params := url.Values{}
	params.Set("when", string(when))
	if zone != "" {
		params.Set("timezone", string(zone))
	}
	applyLimit(params, limit)
	var events []Event
	if err := c.get(ctx, withQuery("/events", params), &events); err != nil {
		return nil, err
	}
	return events, nil
}

// GetEvent returns a single event (GET /events/{id}). Missing is 404.
func (c *Client) GetEvent(ctx context.Context, id int) (Event, error) {
	var event Event
	if err := c.get(ctx, fmt.Sprintf("/events/%d", id), &event); err != nil {
		return Event{}, err
	}
	return event, nil
}

// CreateEvent creates an event (POST /events).
func (c *Client) CreateEvent(ctx context.Context, in EventCreateInput) (Event, error) {
	var event Event
	if err := c.send(ctx, http.MethodPost, "/events", in, &event); err != nil {
		return Event{}, err
	}
	return event, nil
}

// UpdateEvent applies a partial update (PATCH /events/{id}).
func (c *Client) UpdateEvent(ctx context.Context, id int, in EventUpdateInput) (Event, error) {
	var event Event
	if err := c.send(ctx, http.MethodPatch, fmt.Sprintf("/events/%d", id), in, &event); err != nil {
		return Event{}, err
	}
	return event, nil
}

// DeleteEvent removes an event (DELETE /events/{id} → 204).
func (c *Client) DeleteEvent(ctx context.Context, id int) error {
	return c.send(ctx, http.MethodDelete, fmt.Sprintf("/events/%d", id), nil, nil)
}

// AttendEvent marks an event as attending (PATCH /events/{id}/attend).
func (c *Client) AttendEvent(ctx context.Context, id int) (Event, error) {
	var event Event
	if err := c.send(ctx, http.MethodPatch, fmt.Sprintf("/events/%d/attend", id), nil, &event); err != nil {
		return Event{}, err
	}
	return event, nil
}
