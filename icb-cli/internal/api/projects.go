package api

import (
	"context"
	"net/http"
	"net/url"
	"time"
)

// Project mirrors the API's project JSON. Only the fields the CLI renders are
// decoded; unknown fields are ignored, so the server can add columns without
// breaking the client. ItemCount is a pointer because the list/read endpoints
// include it but create/update responses omit it — omitempty keeps `--json`
// faithful to what the server actually sent. Description is nullable.
type Project struct {
	ID          string    `json:"id"`
	Name        string    `json:"name"`
	Description *string   `json:"description"`
	Position    int       `json:"position"`
	CreatedAt   time.Time `json:"created_at"`
	ItemCount   *int      `json:"item_count,omitempty"`
}

// ProjectItemInProject is a project item as seen within a project's ordered
// list (GET /projects/{id}/items/), carrying its position in that project.
type ProjectItemInProject struct {
	ID        string    `json:"id"`
	Title     string    `json:"title"`
	Notes     *string   `json:"notes"`
	Completed bool      `json:"completed"`
	Archived  bool      `json:"archived"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
	Position  int       `json:"position"`
}

// ProjectCreateInput is the body for creating a project. Only Name is required;
// the API defaults Position to 0 and generates the UUID7 id. omitempty keeps
// unset fields out of the payload so the server applies its defaults.
type ProjectCreateInput struct {
	Name        string  `json:"name"`
	Description *string `json:"description,omitempty"`
	Position    *int    `json:"position,omitempty"`
}

// ProjectUpdateInput is a partial update (PATCH /projects/{id}/): every field is
// a pointer with omitempty, so only the fields the user actually changed are
// sent and the server leaves the rest untouched.
type ProjectUpdateInput struct {
	Name        *string `json:"name,omitempty"`
	Description *string `json:"description,omitempty"`
	Position    *int    `json:"position,omitempty"`
}

// ListProjects returns every project with its item count (GET /projects/),
// ordered by position.
func (c *Client) ListProjects(ctx context.Context) ([]Project, error) {
	var projects []Project
	if err := c.get(ctx, "/projects/", &projects); err != nil {
		return nil, err
	}
	return projects, nil
}

// GetProject returns a single project with its item count (GET /projects/{id}/).
// A missing id surfaces as an *APIError with StatusCode 404.
func (c *Client) GetProject(ctx context.Context, id string) (Project, error) {
	var project Project
	if err := c.get(ctx, "/projects/"+id+"/", &project); err != nil {
		return Project{}, err
	}
	return project, nil
}

// CreateProject creates a project (POST /projects/) and returns the created row.
func (c *Client) CreateProject(ctx context.Context, in ProjectCreateInput) (Project, error) {
	var project Project
	if err := c.send(ctx, http.MethodPost, "/projects/", in, &project); err != nil {
		return Project{}, err
	}
	return project, nil
}

// UpdateProject applies a partial update (PATCH /projects/{id}/) and returns the
// updated project. A missing id surfaces as an *APIError with StatusCode 404.
func (c *Client) UpdateProject(ctx context.Context, id string, in ProjectUpdateInput) (Project, error) {
	var project Project
	if err := c.send(ctx, http.MethodPatch, "/projects/"+id+"/", in, &project); err != nil {
		return Project{}, err
	}
	return project, nil
}

// DeleteProject removes a project (DELETE /projects/{id}/ → 204). The API guards
// the delete: a project with incomplete items that belong only to it returns
// 409, which surfaces as an *APIError with StatusCode 409. A missing id is 404.
func (c *Client) DeleteProject(ctx context.Context, id string) error {
	return c.send(ctx, http.MethodDelete, "/projects/"+id+"/", nil, nil)
}

// ListProjectItems returns a project's items in order (GET /projects/{id}/items/).
// When archived is true, archived items are included. A missing id is a 404.
func (c *Client) ListProjectItems(ctx context.Context, id string, archived bool) ([]ProjectItemInProject, error) {
	path := "/projects/" + id + "/items/"
	if archived {
		path += "?" + url.Values{"archived": {"true"}}.Encode()
	}
	var items []ProjectItemInProject
	if err := c.get(ctx, path, &items); err != nil {
		return nil, err
	}
	return items, nil
}
