package api

import (
	"context"
	"net/http"
	"time"
)

// ProjectItemTask mirrors a project item's sub-task JSON. These are the checklist
// tasks under a project item (distinct from the standalone Tasks app). An item
// cannot be completed while it has incomplete tasks.
type ProjectItemTask struct {
	ID        string    `json:"id"`
	ItemID    string    `json:"item_id"`
	Title     string    `json:"title"`
	Completed bool      `json:"completed"`
	Position  int       `json:"position"`
	CreatedAt time.Time `json:"created_at"`
}

// ProjectItemTaskCreateInput is the body for creating a task on an item. Only
// Title is required; the API auto-assigns Position when omitted (0).
type ProjectItemTaskCreateInput struct {
	Title    string `json:"title"`
	Position *int   `json:"position,omitempty"`
}

// ProjectItemTaskUpdateInput is a partial update: only changed fields are sent.
type ProjectItemTaskUpdateInput struct {
	Title     *string `json:"title,omitempty"`
	Completed *bool   `json:"completed,omitempty"`
	Position  *int    `json:"position,omitempty"`
}

// ListItemTasks returns an item's tasks in order
// (GET /project-items/{itemID}/tasks/).
func (c *Client) ListItemTasks(ctx context.Context, itemID string) ([]ProjectItemTask, error) {
	var tasks []ProjectItemTask
	if err := c.get(ctx, "/project-items/"+itemID+"/tasks/", &tasks); err != nil {
		return nil, err
	}
	return tasks, nil
}

// CreateItemTask adds a task to an item (POST /project-items/{itemID}/tasks/).
func (c *Client) CreateItemTask(ctx context.Context, itemID string, in ProjectItemTaskCreateInput) (ProjectItemTask, error) {
	var task ProjectItemTask
	if err := c.send(ctx, http.MethodPost, "/project-items/"+itemID+"/tasks/", in, &task); err != nil {
		return ProjectItemTask{}, err
	}
	return task, nil
}

// UpdateItemTask applies a partial update to a task
// (PATCH /project-items/{itemID}/tasks/{taskID}/). Used for edit and complete.
func (c *Client) UpdateItemTask(ctx context.Context, itemID, taskID string, in ProjectItemTaskUpdateInput) (ProjectItemTask, error) {
	var task ProjectItemTask
	if err := c.send(ctx, http.MethodPatch, "/project-items/"+itemID+"/tasks/"+taskID+"/", in, &task); err != nil {
		return ProjectItemTask{}, err
	}
	return task, nil
}

// DeleteItemTask removes a task (DELETE /project-items/{itemID}/tasks/{taskID}/ → 204).
func (c *Client) DeleteItemTask(ctx context.Context, itemID, taskID string) error {
	return c.send(ctx, http.MethodDelete, "/project-items/"+itemID+"/tasks/"+taskID+"/", nil, nil)
}
