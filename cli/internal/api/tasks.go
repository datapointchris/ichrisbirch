package api

import (
	"context"
	"fmt"
	"net/http"
	"net/url"
	"strconv"
	"time"
)

// Task mirrors the standalone Tasks app JSON (the flat maintenance list, distinct
// from project items). IDs are integers here. CompleteDate and DropDate are
// pointers so an open task (both null) is distinct from a closed one. The
// /completed/ endpoint returns a subset of the same shape, so this one DTO
// covers every read.
//
// RankAt is when the task should reach the top of the open list. The server
// orders by it; the CLI never prints it, because the ranking is meant to be
// silent rather than read as a due date.
type Task struct {
	ID           int        `json:"id"`
	Name         string     `json:"name"`
	Notes        *string    `json:"notes"`
	Category     string     `json:"category"`
	RankAt       time.Time  `json:"rank_at"`
	WindowDays   int        `json:"window_days"`
	Pinned       bool       `json:"pinned"`
	AutoTaskID   *int       `json:"autotask_id"`
	AddDate      time.Time  `json:"add_date"`
	CompleteDate *time.Time `json:"complete_date"`
	DropDate     *time.Time `json:"drop_date"`
	DropReason   *string    `json:"drop_reason"`
}

// Completed reports whether the task has been finished (complete_date is set).
func (t Task) Completed() bool { return t.CompleteDate != nil }

// Dropped reports whether the task was let go (drop_date is set).
func (t Task) Dropped() bool { return t.DropDate != nil }

// TaskCreateInput is the body for creating a task. Name and Category are
// required. An omitted WindowDays takes the category's window server-side.
type TaskCreateInput struct {
	Name       string  `json:"name"`
	Notes      *string `json:"notes,omitempty"`
	Category   string  `json:"category"`
	WindowDays *int    `json:"window_days,omitempty"`
	Pinned     *bool   `json:"pinned,omitempty"`
}

// TaskUpdateInput is a partial update (PATCH /tasks/{id}/): only changed fields
// are sent. Completing, dropping and snoozing have dedicated calls.
type TaskUpdateInput struct {
	Name       *string `json:"name,omitempty"`
	Notes      *string `json:"notes,omitempty"`
	Category   *string `json:"category,omitempty"`
	WindowDays *int    `json:"window_days,omitempty"`
	Pinned     *bool   `json:"pinned,omitempty"`
}

// A task is open, completed or dropped.
const (
	TaskStatusOpen      = "open"
	TaskStatusCompleted = "completed"
	TaskStatusDropped   = "dropped"
	TaskStatusAll       = "all"
)

// TaskStatuses is what --status accepts, lifecycle first then the escape hatch.
var TaskStatuses = []string{TaskStatusOpen, TaskStatusCompleted, TaskStatusDropped, TaskStatusAll}

// TaskCategories mirrors the task_categories lookup table's names, so a flag can
// be checked and offered as choices without a round trip. The spelling is the
// table's, because tasks.category is a foreign key onto it. Each category's
// window lives in the table and is read with ListTaskCategories.
//
// The Vue stores hold the same list for the same reason.
var TaskCategories = []string{
	"Automotive",
	"Chore",
	"Computer",
	"Dingo",
	"Financial",
	"Home",
	"Kitchen",
	"Learn",
	"Personal",
	"Purchase",
	"Research",
	"Work",
}

// TaskCategory is one row of the task_categories table: the name and the window
// a new task in it gets.
type TaskCategory struct {
	Name       string `json:"name"`
	WindowDays int    `json:"window_days"`
}

// ListTasks returns tasks in one status (GET /tasks/). A nil limit fetches all;
// a non-nil limit caps the count. An empty status takes the API's default, open.
// An empty category lists every category. start and end narrow to tasks
// closed within an inclusive range, read in zone.
//
// Every filter is sent rather than applied here, so limit caps the set that was
// asked for. Both strings are validated by the API, so an argument passed in the
// wrong slot comes back a 422 rather than quietly listing the wrong thing.
//
// Open tasks come back in queue order. Completed and dropped tasks come back
// most recently closed first, since a place in the queue stops meaning anything
// once a task leaves it.
func (c *Client) ListTasks(ctx context.Context, limit *int, taskStatus, category string, start OnOrAfter, end OnOrBefore, zone DayZone) ([]Task, error) {
	query := url.Values{}
	if limit != nil {
		query.Set("limit", strconv.Itoa(*limit))
	}
	if taskStatus != "" {
		query.Set("status", taskStatus)
	}
	if category != "" {
		query.Set("category", category)
	}
	applyDateBounds(query, start, end, zone)
	var tasks []Task
	if err := c.get(ctx, withQuery("/tasks/", query), &tasks); err != nil {
		return nil, err
	}
	return tasks, nil
}

// SearchTasks returns tasks whose name or notes match q (GET /tasks/search/?q=).
func (c *Client) SearchTasks(ctx context.Context, q string) ([]Task, error) {
	path := "/tasks/search/?" + url.Values{"q": {q}}.Encode()
	var tasks []Task
	if err := c.get(ctx, path, &tasks); err != nil {
		return nil, err
	}
	return tasks, nil
}

// GetTask returns a single task (GET /tasks/{id}/). A missing id is a 404.
func (c *Client) GetTask(ctx context.Context, id int) (Task, error) {
	var task Task
	if err := c.get(ctx, fmt.Sprintf("/tasks/%d/", id), &task); err != nil {
		return Task{}, err
	}
	return task, nil
}

// CreateTask creates a task (POST /tasks/) and returns the created row.
func (c *Client) CreateTask(ctx context.Context, in TaskCreateInput) (Task, error) {
	var task Task
	if err := c.send(ctx, http.MethodPost, "/tasks/", in, &task); err != nil {
		return Task{}, err
	}
	return task, nil
}

// UpdateTask applies a partial update (PATCH /tasks/{id}/).
func (c *Client) UpdateTask(ctx context.Context, id int, in TaskUpdateInput) (Task, error) {
	var task Task
	if err := c.send(ctx, http.MethodPatch, fmt.Sprintf("/tasks/%d/", id), in, &task); err != nil {
		return Task{}, err
	}
	return task, nil
}

// SetTaskPinned pins or unpins a task. A pinned task sorts ahead of every
// unpinned one.
func (c *Client) SetTaskPinned(ctx context.Context, id int, pinned bool) (Task, error) {
	return c.UpdateTask(ctx, id, TaskUpdateInput{Pinned: &pinned})
}

// DeleteTask removes a task (DELETE /tasks/{id}/ → 204).
func (c *Client) DeleteTask(ctx context.Context, id int) error {
	return c.send(ctx, http.MethodDelete, fmt.Sprintf("/tasks/%d/", id), nil, nil)
}

// CompleteTask stamps a task's completion time (PATCH /tasks/{id}/complete/).
// A task already closed answers 409.
func (c *Client) CompleteTask(ctx context.Context, id int) (Task, error) {
	return c.taskAction(ctx, id, "complete", nil)
}

// SnoozeTask restarts the task's window from now and unpins it
// (PATCH /tasks/{id}/snooze/), which moves it back down the list.
func (c *Client) SnoozeTask(ctx context.Context, id int) (Task, error) {
	return c.taskAction(ctx, id, "snooze", nil)
}

// DropTask closes a task that is being let go (PATCH /tasks/{id}/drop/). It
// stays on record and does not count as completed. An empty reason sends none.
func (c *Client) DropTask(ctx context.Context, id int, reason string) (Task, error) {
	body := struct {
		Reason *string `json:"reason,omitempty"`
	}{}
	if reason != "" {
		body.Reason = &reason
	}
	return c.taskAction(ctx, id, "drop", body)
}

// ReopenTask returns a completed or dropped task to the open list
// (PATCH /tasks/{id}/reopen/), clearing its closing date and drop reason
// together. A task already open answers 409.
func (c *Client) ReopenTask(ctx context.Context, id int) (Task, error) {
	return c.taskAction(ctx, id, "reopen", nil)
}

func (c *Client) taskAction(ctx context.Context, id int, action string, body any) (Task, error) {
	var task Task
	if err := c.send(ctx, http.MethodPatch, fmt.Sprintf("/tasks/%d/%s/", id, action), body, &task); err != nil {
		return Task{}, err
	}
	return task, nil
}

// ListTaskCategories returns every task category with its window
// (GET /tasks/categories/).
func (c *Client) ListTaskCategories(ctx context.Context) ([]TaskCategory, error) {
	var categories []TaskCategory
	if err := c.get(ctx, "/tasks/categories/", &categories); err != nil {
		return nil, err
	}
	return categories, nil
}

// UpdateTaskCategory sets a category's window (PATCH /tasks/categories/{name}/).
// Tasks already open keep the window they were made with.
func (c *Client) UpdateTaskCategory(ctx context.Context, name string, windowDays int) (TaskCategory, error) {
	body := struct {
		WindowDays int `json:"window_days"`
	}{windowDays}
	var category TaskCategory
	if err := c.send(ctx, http.MethodPatch, "/tasks/categories/"+url.PathEscape(name)+"/", body, &category); err != nil {
		return TaskCategory{}, err
	}
	return category, nil
}
