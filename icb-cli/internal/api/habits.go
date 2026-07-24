package api

import (
	"context"
	"fmt"
	"net/http"
	"net/url"
	"strconv"
	"time"
)

// HabitCategory is a habit's category (a lookup row).
type HabitCategory struct {
	ID        int    `json:"id"`
	Name      string `json:"name"`
	IsCurrent bool   `json:"is_current"`
}

// Habit mirrors the habits JSON. Category is the embedded category row; IsCurrent
// marks whether the habit is actively tracked.
type Habit struct {
	ID         int           `json:"id"`
	Name       string        `json:"name"`
	CategoryID int           `json:"category_id"`
	Category   HabitCategory `json:"category"`
	IsCurrent  bool          `json:"is_current"`
}

// HabitCompleted is a recorded completion of a habit on a date.
type HabitCompleted struct {
	ID           int           `json:"id"`
	Name         string        `json:"name"`
	CategoryID   int           `json:"category_id"`
	Category     HabitCategory `json:"category"`
	CompleteDate time.Time     `json:"complete_date"`
}

// HabitCreateInput is the body for creating a habit. Name and CategoryID are
// required; IsCurrent defaults to true server-side when omitted.
type HabitCreateInput struct {
	Name       string `json:"name"`
	CategoryID int    `json:"category_id"`
	IsCurrent  *bool  `json:"is_current,omitempty"`
}

// HabitUpdateInput is a partial update (PATCH /habits/{id}/).
type HabitUpdateInput struct {
	Name       *string `json:"name,omitempty"`
	CategoryID *int    `json:"category_id,omitempty"`
	IsCurrent  *bool   `json:"is_current,omitempty"`
}

// HabitCompletedCreateInput records a completion (POST /habits/completed/).
// CompleteDate is a datetime string parsed server-side.
type HabitCompletedCreateInput struct {
	Name         string `json:"name"`
	CategoryID   int    `json:"category_id"`
	CompleteDate string `json:"complete_date"`
}

// ListHabits returns habits (GET /habits/). current filters to current-only
// (true) or non-current-only (false); nil returns all. limit caps the count.
func (c *Client) ListHabits(ctx context.Context, current *bool, limit *int) ([]Habit, error) {
	var habits []Habit
	if err := c.get(ctx, "/habits/"+currentLimitQuery(current, limit), &habits); err != nil {
		return nil, err
	}
	return habits, nil
}

// GetHabit returns a single habit (GET /habits/{id}/). Missing is 404.
func (c *Client) GetHabit(ctx context.Context, id int) (Habit, error) {
	var habit Habit
	if err := c.get(ctx, fmt.Sprintf("/habits/%d/", id), &habit); err != nil {
		return Habit{}, err
	}
	return habit, nil
}

// CreateHabit creates a habit (POST /habits/).
func (c *Client) CreateHabit(ctx context.Context, in HabitCreateInput) (Habit, error) {
	var habit Habit
	if err := c.send(ctx, http.MethodPost, "/habits/", in, &habit); err != nil {
		return Habit{}, err
	}
	return habit, nil
}

// UpdateHabit applies a partial update (PATCH /habits/{id}/).
func (c *Client) UpdateHabit(ctx context.Context, id int, in HabitUpdateInput) (Habit, error) {
	var habit Habit
	if err := c.send(ctx, http.MethodPatch, fmt.Sprintf("/habits/%d/", id), in, &habit); err != nil {
		return Habit{}, err
	}
	return habit, nil
}

// DeleteHabit removes a habit (DELETE /habits/{id}/ → 204).
func (c *Client) DeleteHabit(ctx context.Context, id int) error {
	return c.send(ctx, http.MethodDelete, fmt.Sprintf("/habits/%d/", id), nil, nil)
}

// ListHabitCategories returns habit categories (GET /habits/categories/), with
// the same current/limit filters as habits.
func (c *Client) ListHabitCategories(ctx context.Context, current *bool, limit *int) ([]HabitCategory, error) {
	var categories []HabitCategory
	if err := c.get(ctx, "/habits/categories/"+currentLimitQuery(current, limit), &categories); err != nil {
		return nil, err
	}
	return categories, nil
}

// CompleteHabit records a habit completion (POST /habits/completed/).
func (c *Client) CompleteHabit(ctx context.Context, in HabitCompletedCreateInput) (HabitCompleted, error) {
	var completed HabitCompleted
	if err := c.send(ctx, http.MethodPost, "/habits/completed/", in, &completed); err != nil {
		return HabitCompleted{}, err
	}
	return completed, nil
}

// ListCompletedHabits returns habit completions (GET /habits/completed/),
// filtered by the same query as completed tasks.
func (c *Client) ListCompletedHabits(ctx context.Context, q CompletedTasksQuery) ([]HabitCompleted, error) {
	params := url.Values{}
	if q.StartDate != "" {
		params.Set("start_date", q.StartDate)
	}
	if q.EndDate != "" {
		params.Set("end_date", q.EndDate)
	}
	if q.First {
		params.Set("first", "true")
	}
	if q.Last {
		params.Set("last", "true")
	}
	path := "/habits/completed/"
	if encoded := params.Encode(); encoded != "" {
		path += "?" + encoded
	}
	var completed []HabitCompleted
	if err := c.get(ctx, path, &completed); err != nil {
		return nil, err
	}
	return completed, nil
}

// currentLimitQuery builds the shared ?current=&limit= query string for the
// habits and categories list endpoints.
func currentLimitQuery(current *bool, limit *int) string {
	params := url.Values{}
	if current != nil {
		params.Set("current", strconv.FormatBool(*current))
	}
	if limit != nil {
		params.Set("limit", strconv.Itoa(*limit))
	}
	if encoded := params.Encode(); encoded != "" {
		return "?" + encoded
	}
	return ""
}
