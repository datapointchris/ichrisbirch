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
// from project items). IDs are integers here. CompleteDate is a pointer so an
// incomplete task (null) is distinct from a completed one. The /completed/
// endpoint returns the same shape (its extra @property fields are not
// serialized), so this one DTO covers every read.
type Task struct {
	ID           int        `json:"id"`
	Name         string     `json:"name"`
	Notes        *string    `json:"notes"`
	Category     string     `json:"category"`
	Priority     int        `json:"priority"`
	AddDate      time.Time  `json:"add_date"`
	CompleteDate *time.Time `json:"complete_date"`
}

// Completed reports whether the task has been finished (complete_date is set).
func (t Task) Completed() bool { return t.CompleteDate != nil }

// TaskCreateInput is the body for creating a task. Name and Category are
// required; Priority defaults to 1 server-side when omitted.
type TaskCreateInput struct {
	Name     string  `json:"name"`
	Notes    *string `json:"notes,omitempty"`
	Category string  `json:"category"`
	Priority *int    `json:"priority,omitempty"`
}

// TaskUpdateInput is a partial update (PATCH /tasks/{id}/): only changed fields
// are sent. Completion is handled by the dedicated CompleteTask call.
type TaskUpdateInput struct {
	Name     *string `json:"name,omitempty"`
	Notes    *string `json:"notes,omitempty"`
	Category *string `json:"category,omitempty"`
	Priority *int    `json:"priority,omitempty"`
}

// CompletedTasksQuery filters the /tasks/completed/ endpoint. First/Last return
// the single earliest/most-recent completed task; StartDate/EndDate bound a range
// (ISO 8601). All are optional; with none set, every completed task is returned.
type CompletedTasksQuery struct {
	StartDate string
	EndDate   string
	First     bool
	Last      bool
}

// ListTasks returns tasks ordered by priority (GET /tasks/). A nil limit fetches
// all; a non-nil limit caps the count.
func (c *Client) ListTasks(ctx context.Context, limit *int) ([]Task, error) {
	return c.listTasks(ctx, "/tasks/", limit)
}

// ListTodoTasks returns incomplete tasks ordered by priority (GET /tasks/todo/).
func (c *Client) ListTodoTasks(ctx context.Context, limit *int) ([]Task, error) {
	return c.listTasks(ctx, "/tasks/todo/", limit)
}

func (c *Client) listTasks(ctx context.Context, base string, limit *int) ([]Task, error) {
	if limit != nil {
		base += "?" + url.Values{"limit": {strconv.Itoa(*limit)}}.Encode()
	}
	var tasks []Task
	if err := c.get(ctx, base, &tasks); err != nil {
		return nil, err
	}
	return tasks, nil
}

// ListCompletedTasks returns completed tasks (GET /tasks/completed/), filtered by
// the given query.
func (c *Client) ListCompletedTasks(ctx context.Context, q CompletedTasksQuery) ([]Task, error) {
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
	path := "/tasks/completed/"
	if encoded := params.Encode(); encoded != "" {
		path += "?" + encoded
	}
	var tasks []Task
	if err := c.get(ctx, path, &tasks); err != nil {
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

// DeleteTask removes a task (DELETE /tasks/{id}/ → 204).
func (c *Client) DeleteTask(ctx context.Context, id int) error {
	return c.send(ctx, http.MethodDelete, fmt.Sprintf("/tasks/%d/", id), nil, nil)
}

// CompleteTask stamps a task's completion time (PATCH /tasks/{id}/complete/).
func (c *Client) CompleteTask(ctx context.Context, id int) (Task, error) {
	var task Task
	if err := c.send(ctx, http.MethodPatch, fmt.Sprintf("/tasks/%d/complete/", id), nil, &task); err != nil {
		return Task{}, err
	}
	return task, nil
}

// ShiftTask shifts a task's priority rank by positions (PATCH
// /tasks/{id}/shift/{positions}/): positive pushes it down, negative pulls it up.
func (c *Client) ShiftTask(ctx context.Context, id, positions int) (Task, error) {
	var task Task
	if err := c.send(ctx, http.MethodPatch, fmt.Sprintf("/tasks/%d/shift/%d/", id, positions), nil, &task); err != nil {
		return Task{}, err
	}
	return task, nil
}

// ReorderTasks dense-ranks incomplete task priorities to 1..K (POST
// /tasks/reorder/) and returns the server's status message.
func (c *Client) ReorderTasks(ctx context.Context) (string, error) {
	var out struct {
		Message string `json:"message"`
	}
	if err := c.send(ctx, http.MethodPost, "/tasks/reorder/", nil, &out); err != nil {
		return "", err
	}
	return out.Message, nil
}
