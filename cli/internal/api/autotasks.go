package api

import (
	"context"
	"fmt"
	"net/url"
	"time"
)

// AutoTask mirrors the autotasks JSON — a recurring task template the scheduler
// uses to spawn tasks. It is read-only from the CLI: the scheduler owns the
// run bookkeeping (first_run_date/last_run_date/run_count). notes is nullable.
//
// WindowDays is the window each copy gets, nil meaning the category's. Anchor is
// "completion" (the next copy counts from the later of the last close and the
// last run) or "calendar" (fixed steps from the first run).
type AutoTask struct {
	ID            int       `json:"id"`
	Name          string    `json:"name"`
	Category      string    `json:"category"`
	Notes         *string   `json:"notes"`
	Frequency     string    `json:"frequency"`
	WindowDays    *int      `json:"window_days"`
	Anchor        string    `json:"anchor"`
	MaxConcurrent int       `json:"max_concurrent"`
	FirstRunDate  time.Time `json:"first_run_date"`
	LastRunDate   time.Time `json:"last_run_date"`
	RunCount      int       `json:"run_count"`
}

// ListAutoTasks returns recurring task templates, most recently run first
// (GET /autotasks/). A nil limit fetches all; a non-nil limit caps the count.
func (c *Client) ListAutoTasks(ctx context.Context, limit *int) ([]AutoTask, error) {
	params := url.Values{}
	applyLimit(params, limit)
	var autotasks []AutoTask
	if err := c.get(ctx, withQuery("/autotasks/", params), &autotasks); err != nil {
		return nil, err
	}
	return autotasks, nil
}

// GetAutoTask returns a single recurring task template (GET /autotasks/{id}/).
// Missing is 404.
func (c *Client) GetAutoTask(ctx context.Context, id int) (AutoTask, error) {
	var autotask AutoTask
	if err := c.get(ctx, fmt.Sprintf("/autotasks/%d/", id), &autotask); err != nil {
		return AutoTask{}, err
	}
	return autotask, nil
}
