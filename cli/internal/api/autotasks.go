package api

import (
	"context"
	"fmt"
	"time"
)

// AutoTask mirrors the autotasks JSON — a recurring task template the scheduler
// uses to spawn tasks. It is read-only from the CLI: the scheduler owns the
// run bookkeeping (first_run_date/last_run_date/run_count). notes is nullable.
type AutoTask struct {
	ID            int       `json:"id"`
	Name          string    `json:"name"`
	Category      string    `json:"category"`
	Priority      int       `json:"priority"`
	Notes         *string   `json:"notes"`
	Frequency     string    `json:"frequency"`
	MaxConcurrent int       `json:"max_concurrent"`
	FirstRunDate  time.Time `json:"first_run_date"`
	LastRunDate   time.Time `json:"last_run_date"`
	RunCount      int       `json:"run_count"`
}

// ListAutoTasks returns all recurring task templates (GET /autotasks/).
func (c *Client) ListAutoTasks(ctx context.Context) ([]AutoTask, error) {
	var autotasks []AutoTask
	if err := c.get(ctx, "/autotasks/", &autotasks); err != nil {
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
