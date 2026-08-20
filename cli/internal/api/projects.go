package api

import (
	"context"
	"net/http"
	"net/url"
	"time"
)

// Project mirrors the API's project JSON. Only the fields the CLI renders are
// decoded; unknown fields are ignored, so the server can add columns without
// breaking the client. The counts are pointers because the list/read endpoints
// include them but create/update responses omit them — omitempty keeps `--json`
// faithful to what the server actually sent. Description is nullable.
//
// OpenCount and CompletedCount exclude archived items, so they sum to ItemCount
// only when nothing in the project is archived.
//
// Repos is derived server-side from the items' repo tags, not a column on the
// project — one source of truth, and a project spanning an API, a CLI, and a TUI
// lists all three.
//
// Status is active/done/dropped. ClosedAt and StatusReason are set by the
// server as consequences of the transition, never sent by the client.
type Project struct {
	ID             string     `json:"id"`
	Name           string     `json:"name"`
	Description    *string    `json:"description"`
	Kind           string     `json:"kind"`
	Status         string     `json:"status"`
	StatusReason   *string    `json:"status_reason"`
	ClosedAt       *time.Time `json:"closed_at"`
	Position       int        `json:"position"`
	CreatedAt      time.Time  `json:"created_at"`
	ItemCount      *int       `json:"item_count,omitempty"`
	OpenCount      *int       `json:"open_count,omitempty"`
	CompletedCount *int       `json:"completed_count,omitempty"`
	Repos          []string   `json:"repos,omitempty"`
}

// ProjectItemInProject is a project item as seen within a project's ordered
// list (GET /projects/{id}/items/), carrying its position in that project.
type ProjectItemInProject struct {
	ID        string    `json:"id"`
	Number    int       `json:"number"`
	Title     string    `json:"title"`
	Notes     *string   `json:"notes"`
	Repo      *string   `json:"repo"`
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
	Kind        *string `json:"kind,omitempty"`
	Position    *int    `json:"position,omitempty"`
}

// ProjectUpdateInput is a partial update (PATCH /projects/{id}/): every field is
// a pointer with omitempty, so only the fields the user actually changed are
// sent and the server leaves the rest untouched.
//
// ClosedAt is absent deliberately — the server stamps it on the transition into
// a terminal status and clears it on reopen, so it cannot drift from the status
// it describes.
type ProjectUpdateInput struct {
	Name         *string `json:"name,omitempty"`
	Description  *string `json:"description,omitempty"`
	Kind         *string `json:"kind,omitempty"`
	Status       *string `json:"status,omitempty"`
	StatusReason *string `json:"status_reason,omitempty"`
	Position     *int    `json:"position,omitempty"`
}

// AllProjectStatuses asks for every project regardless of status. Not a status
// itself — it is the absence of the filter, which is why the server keeps it out
// of the lookup table.
const AllProjectStatuses = "all"

// ListProjects returns projects with their item counts (GET /projects/). An
// empty projectStatus takes the server's default, which is the active projects
// only; pass a status name or AllProjectStatuses to see the closed ones.
func (c *Client) ListProjects(ctx context.Context, repo *string, projectStatus string) ([]Project, error) {
	query := repoQuery(repo)
	if projectStatus != "" {
		query.Set("status", projectStatus)
	}
	var projects []Project
	if err := c.get(ctx, withQuery("/projects/", query), &projects); err != nil {
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

// The statuses a project can be in. Stored, unlike an item's, because for a
// project completion and hiding are the same event — so there is nothing to
// archive separately and `dropped` carries what was abandoned rather than
// finished.
//
// `completed` and not `done`: an item stores a `completed` boolean and every
// reader renders that word, so one concept spelled two ways on a resource and
// its own children was the mismatch this removed.
const (
	ProjectStatusActive    = "active"
	ProjectStatusCompleted = "completed"
	ProjectStatusDropped   = "dropped"
	ProjectStatusAll       = "all"
)

// ProjectStatuses is what --status accepts: the lifecycle in order, then the
// escape hatch.
var ProjectStatuses = []string{ProjectStatusActive, ProjectStatusCompleted, ProjectStatusDropped, ProjectStatusAll}

// What sort of work a project is. `kind` separates making something new from
// the work that merely has to happen, which is what lets `items next` weight a
// build differently from a chore.
//
// The API's project_kinds table is the authority and rejects anything else.
// These are here so the flag help, the guided form, and its default all read
// one list.
const (
	ProjectKindBuild = "build"
	ProjectKindChore = "chore"
	ProjectKindLife  = "life"
)

// ProjectKinds is what --kind accepts, in the order the form offers them.
var ProjectKinds = []string{ProjectKindBuild, ProjectKindChore, ProjectKindLife}

// ListProjectItems returns a project's items in order (GET /projects/{id}/items/),
// narrowed to one derived status. It takes the same vocabulary as ListItems
// because scoping to a project picks which rows come back and not which states.
// An empty itemStatus leaves the server's default. A missing id is a 404.
func (c *Client) ListProjectItems(ctx context.Context, id, itemStatus string) ([]ProjectItemInProject, error) {
	path := "/projects/" + id + "/items/"
	if itemStatus != "" {
		path += "?" + url.Values{"status": {itemStatus}}.Encode()
	}
	var items []ProjectItemInProject
	if err := c.get(ctx, path, &items); err != nil {
		return nil, err
	}
	return items, nil
}
