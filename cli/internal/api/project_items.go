package api

import (
	"context"
	"net/http"
	"net/url"
	"time"
)

// ProjectItem mirrors the API's project-item JSON as returned by the list,
// search, blocked, and blockers endpoints (schemas.ProjectItem). Only rendered
// fields are decoded; unknown fields are ignored.
//
// Projects rides along on every list response: an item title alone names a thing
// without saying what work it belongs to.
type ProjectItem struct {
	ID string `json:"id"`
	// Number is the handle: server-assigned, short, and what every command
	// prints and accepts. ID stays the key and is only useful to a caller
	// holding it from --json.
	Number    int       `json:"number"`
	Title     string    `json:"title"`
	Notes     *string   `json:"notes"`
	Repo      *string   `json:"repo"`
	Completed bool      `json:"completed"`
	Archived  bool      `json:"archived"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
	Projects  []Project `json:"projects"`
	// DependencyIDs rides along on every row, so the whole dependency graph
	// arrives in one request. Reaching it through the detail endpoint instead
	// costs a request per item, and answering "what blocks what" then scales
	// with the store rather than with the question.
	DependencyIDs []string `json:"dependency_ids"`
}

// ProjectItemDetail is the extended view (GET /project-items/{id}/, and the
// create / add-dependency responses): the item plus the projects it belongs to
// and the ids of the items it depends on.
type ProjectItemDetail struct {
	ID            string    `json:"id"`
	Number        int       `json:"number"`
	Title         string    `json:"title"`
	Notes         *string   `json:"notes"`
	Repo          *string   `json:"repo"`
	Completed     bool      `json:"completed"`
	Archived      bool      `json:"archived"`
	CreatedAt     time.Time `json:"created_at"`
	UpdatedAt     time.Time `json:"updated_at"`
	Projects      []Project `json:"projects"`
	DependencyIDs []string  `json:"dependency_ids"`
}

// ProjectItemCreateInput is the body for creating a project item. Title and at
// least one ProjectID are required by the API (a 422 otherwise).
type ProjectItemCreateInput struct {
	Title      string   `json:"title"`
	Notes      *string  `json:"notes,omitempty"`
	Repo       *string  `json:"repo,omitempty"`
	ProjectIDs []string `json:"project_ids"`
}

// ProjectItemUpdateInput is a partial update (PATCH /project-items/{id}/): every
// field is a pointer with omitempty, so only changed fields are sent. Completing
// (Completed=true) is refused by the API (400) while the item has incomplete
// tasks.
type ProjectItemUpdateInput struct {
	Title     *string `json:"title,omitempty"`
	Notes     *string `json:"notes,omitempty"`
	Repo      *string `json:"repo,omitempty"`
	Completed *bool   `json:"completed,omitempty"`
	Archived  *bool   `json:"archived,omitempty"`
}

// ProjectItemReorderInput moves an item to a new position within a specific
// project (PATCH /project-items/{id}/reorder/).
type ProjectItemReorderInput struct {
	ProjectID string `json:"project_id"`
	Position  int    `json:"position"`
}

// ProjectMembershipInput adds an item to a project (POST /project-items/{id}/projects/).
type ProjectMembershipInput struct {
	ProjectID string `json:"project_id"`
}

// DependencyInput records that an item depends on another
// (POST /project-items/{id}/dependencies/).
type DependencyInput struct {
	DependsOnID string `json:"depends_on_id"`
}

// ListItems returns project items in one status (GET /project-items/).
//
// An empty status takes the API's default, which is open. Pass a status to ask
// for another, or ItemStatusAll for every one.
func (c *Client) ListItems(ctx context.Context, repo *string, itemStatus string) ([]ProjectItem, error) {
	query := repoQuery(repo)
	if itemStatus != "" {
		query.Set("status", itemStatus)
	}
	var items []ProjectItem
	if err := c.get(ctx, withQuery("/project-items/", query), &items); err != nil {
		return nil, err
	}
	return items, nil
}

// ListBlockedItems returns items with at least one incomplete dependency
// (GET /project-items/blocked/).
func (c *Client) ListBlockedItems(ctx context.Context, repo *string) ([]ProjectItem, error) {
	var items []ProjectItem
	if err := c.get(ctx, withQuery("/project-items/blocked/", repoQuery(repo)), &items); err != nil {
		return nil, err
	}
	return items, nil
}

// SearchItems returns items whose title or notes match q
// (GET /project-items/search/?q=).
func (c *Client) SearchItems(ctx context.Context, q string, repo *string) ([]ProjectItem, error) {
	query := repoQuery(repo)
	query.Set("q", q)
	var items []ProjectItem
	if err := c.get(ctx, withQuery("/project-items/search/", query), &items); err != nil {
		return nil, err
	}
	return items, nil
}

// The statuses an item can be asked for. Derived from `completed` and
// `archived` server-side, with archived beating completed, so the three
// partition every item and no combination answers to two of them.
const (
	ItemStatusOpen      = "open"
	ItemStatusCompleted = "completed"
	ItemStatusArchived  = "archived"
	ItemStatusAll       = "all"
)

// ItemStatuses is what --status accepts, in the order help should list them:
// the lifecycle in order, then the escape hatch.
var ItemStatuses = []string{ItemStatusOpen, ItemStatusCompleted, ItemStatusArchived, ItemStatusAll}

// repoQuery renders the repo filter. A nil pointer asks for everything; a
// pointer to "" asks for the untagged items, which is a different question and
// so has to survive as an explicit empty parameter rather than being dropped.
func repoQuery(repo *string) url.Values {
	query := url.Values{}
	if repo != nil {
		query.Set("repo", *repo)
	}
	return query
}

func withQuery(path string, query url.Values) string {
	if len(query) == 0 {
		return path
	}
	return path + "?" + query.Encode()
}

// GetItem returns a single item's detail (GET /project-items/{id}/). A missing
// id surfaces as an *APIError with StatusCode 404.
func (c *Client) GetItem(ctx context.Context, id string) (ProjectItemDetail, error) {
	var item ProjectItemDetail
	if err := c.get(ctx, "/project-items/"+id+"/", &item); err != nil {
		return ProjectItemDetail{}, err
	}
	return item, nil
}

// CreateItem creates a project item (POST /project-items/) and returns its detail.
func (c *Client) CreateItem(ctx context.Context, in ProjectItemCreateInput) (ProjectItemDetail, error) {
	var item ProjectItemDetail
	if err := c.send(ctx, http.MethodPost, "/project-items/", in, &item); err != nil {
		return ProjectItemDetail{}, err
	}
	return item, nil
}

// UpdateItem applies a partial update (PATCH /project-items/{id}/) and returns
// the updated item. Used for edit, complete/reopen, and archive/unarchive.
func (c *Client) UpdateItem(ctx context.Context, id string, in ProjectItemUpdateInput) (ProjectItem, error) {
	var item ProjectItem
	if err := c.send(ctx, http.MethodPatch, "/project-items/"+id+"/", in, &item); err != nil {
		return ProjectItem{}, err
	}
	return item, nil
}

// DeleteItem removes a project item (DELETE /project-items/{id}/ → 204).
func (c *Client) DeleteItem(ctx context.Context, id string) error {
	return c.send(ctx, http.MethodDelete, "/project-items/"+id+"/", nil, nil)
}

// ReorderItem moves an item within a project (PATCH /project-items/{id}/reorder/)
// and returns the item with its new position in that project.
func (c *Client) ReorderItem(ctx context.Context, id string, in ProjectItemReorderInput) (ProjectItemInProject, error) {
	var item ProjectItemInProject
	if err := c.send(ctx, http.MethodPatch, "/project-items/"+id+"/reorder/", in, &item); err != nil {
		return ProjectItemInProject{}, err
	}
	return item, nil
}

// AddItemToProject adds an item to another project (POST /project-items/{id}/projects/)
// and returns the project it was added to.
func (c *Client) AddItemToProject(ctx context.Context, id string, in ProjectMembershipInput) (Project, error) {
	var project Project
	if err := c.send(ctx, http.MethodPost, "/project-items/"+id+"/projects/", in, &project); err != nil {
		return Project{}, err
	}
	return project, nil
}

// RemoveItemFromProject removes an item from a project
// (DELETE /project-items/{id}/projects/{projectID}/ → 204). The API refuses (409)
// to remove an item from its last project.
func (c *Client) RemoveItemFromProject(ctx context.Context, id, projectID string) error {
	return c.send(ctx, http.MethodDelete, "/project-items/"+id+"/projects/"+projectID+"/", nil, nil)
}

// AddDependency records that item id depends on another item
// (POST /project-items/{id}/dependencies/) and returns the item's updated detail.
// The API rejects self-dependencies (422) and cycles (409).
func (c *Client) AddDependency(ctx context.Context, id string, in DependencyInput) (ProjectItemDetail, error) {
	var item ProjectItemDetail
	if err := c.send(ctx, http.MethodPost, "/project-items/"+id+"/dependencies/", in, &item); err != nil {
		return ProjectItemDetail{}, err
	}
	return item, nil
}

// RemoveDependency removes a dependency edge
// (DELETE /project-items/{id}/dependencies/{depID}/ → 204).
func (c *Client) RemoveDependency(ctx context.Context, id, depID string) error {
	return c.send(ctx, http.MethodDelete, "/project-items/"+id+"/dependencies/"+depID+"/", nil, nil)
}

// GetBlockers returns the incomplete dependencies blocking an item
// (GET /project-items/{id}/blockers/).
func (c *Client) GetBlockers(ctx context.Context, id string) ([]ProjectItem, error) {
	var items []ProjectItem
	if err := c.get(ctx, "/project-items/"+id+"/blockers/", &items); err != nil {
		return nil, err
	}
	return items, nil
}
