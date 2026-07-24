package api

import (
	"context"
	"fmt"
	"net/http"
	"net/url"
	"strconv"
	"time"
)

// CookingTechnique mirrors the cooking-techniques JSON — a durable how-and-why
// writeup nested under the recipes domain (endpoints live at
// /recipes/cooking-techniques/). Nullable prose fields are pointers; slug is
// server-generated from the name.
type CookingTechnique struct {
	ID             int       `json:"id"`
	Name           string    `json:"name"`
	Category       string    `json:"category"`
	Summary        string    `json:"summary"`
	Body           string    `json:"body"`
	WhyItWorks     *string   `json:"why_it_works"`
	CommonPitfalls *string   `json:"common_pitfalls"`
	SourceURL      *string   `json:"source_url"`
	SourceName     *string   `json:"source_name"`
	Tags           []string  `json:"tags"`
	Rating         *int      `json:"rating"`
	Slug           string    `json:"slug"`
	CreatedAt      time.Time `json:"created_at"`
	UpdatedAt      time.Time `json:"updated_at"`
}

// CookingTechniqueCreateInput is the body for POST /recipes/cooking-techniques/.
// name/category/summary/body are required; the rest are optional prose.
type CookingTechniqueCreateInput struct {
	Name           string   `json:"name"`
	Category       string   `json:"category"`
	Summary        string   `json:"summary"`
	Body           string   `json:"body"`
	WhyItWorks     *string  `json:"why_it_works,omitempty"`
	CommonPitfalls *string  `json:"common_pitfalls,omitempty"`
	SourceURL      *string  `json:"source_url,omitempty"`
	SourceName     *string  `json:"source_name,omitempty"`
	Tags           []string `json:"tags,omitempty"`
	Rating         *int     `json:"rating,omitempty"`
}

// CookingTechniqueUpdateInput is a partial update (PATCH
// /recipes/cooking-techniques/{id}/): only the fields set are sent.
type CookingTechniqueUpdateInput struct {
	Name           *string  `json:"name,omitempty"`
	Category       *string  `json:"category,omitempty"`
	Summary        *string  `json:"summary,omitempty"`
	Body           *string  `json:"body,omitempty"`
	WhyItWorks     *string  `json:"why_it_works,omitempty"`
	CommonPitfalls *string  `json:"common_pitfalls,omitempty"`
	SourceURL      *string  `json:"source_url,omitempty"`
	SourceName     *string  `json:"source_name,omitempty"`
	Tags           []string `json:"tags,omitempty"`
	Rating         *int     `json:"rating,omitempty"`
}

// CookingTechniqueCategory is one bucket in the category breakdown (includes
// zero-count categories so every bucket is visible).
type CookingTechniqueCategory struct {
	Name  string `json:"name"`
	Count int    `json:"count"`
}

// ListCookingTechniques returns techniques ordered by name (GET
// /recipes/cooking-techniques/). category and ratingMin, when non-nil, filter.
func (c *Client) ListCookingTechniques(ctx context.Context, category *string, ratingMin *int) ([]CookingTechnique, error) {
	params := url.Values{}
	if category != nil {
		params.Set("category", *category)
	}
	if ratingMin != nil {
		params.Set("rating_min", strconv.Itoa(*ratingMin))
	}
	path := "/recipes/cooking-techniques/"
	if encoded := params.Encode(); encoded != "" {
		path += "?" + encoded
	}
	var techniques []CookingTechnique
	if err := c.get(ctx, path, &techniques); err != nil {
		return nil, err
	}
	return techniques, nil
}

// GetCookingTechnique returns a single technique by id (GET
// /recipes/cooking-techniques/{id}/). Missing is 404.
func (c *Client) GetCookingTechnique(ctx context.Context, id int) (CookingTechnique, error) {
	var technique CookingTechnique
	if err := c.get(ctx, fmt.Sprintf("/recipes/cooking-techniques/%d/", id), &technique); err != nil {
		return CookingTechnique{}, err
	}
	return technique, nil
}

// GetCookingTechniqueBySlug returns a single technique by slug (GET
// /recipes/cooking-techniques/slug/{slug}/). Missing is 404.
func (c *Client) GetCookingTechniqueBySlug(ctx context.Context, slug string) (CookingTechnique, error) {
	var technique CookingTechnique
	if err := c.get(ctx, fmt.Sprintf("/recipes/cooking-techniques/slug/%s/", url.PathEscape(slug)), &technique); err != nil {
		return CookingTechnique{}, err
	}
	return technique, nil
}

// SearchCookingTechniques returns techniques matching q across name, summary,
// body, and tags (GET /recipes/cooking-techniques/search/?q=).
func (c *Client) SearchCookingTechniques(ctx context.Context, q string) ([]CookingTechnique, error) {
	path := "/recipes/cooking-techniques/search/?" + url.Values{"q": {q}}.Encode()
	var techniques []CookingTechnique
	if err := c.get(ctx, path, &techniques); err != nil {
		return nil, err
	}
	return techniques, nil
}

// ListCookingTechniqueCategories returns all category buckets with counts (GET
// /recipes/cooking-techniques/categories/).
func (c *Client) ListCookingTechniqueCategories(ctx context.Context) ([]CookingTechniqueCategory, error) {
	var categories []CookingTechniqueCategory
	if err := c.get(ctx, "/recipes/cooking-techniques/categories/", &categories); err != nil {
		return nil, err
	}
	return categories, nil
}

// CreateCookingTechnique creates a technique (POST /recipes/cooking-techniques/).
func (c *Client) CreateCookingTechnique(ctx context.Context, in CookingTechniqueCreateInput) (CookingTechnique, error) {
	var technique CookingTechnique
	if err := c.send(ctx, http.MethodPost, "/recipes/cooking-techniques/", in, &technique); err != nil {
		return CookingTechnique{}, err
	}
	return technique, nil
}

// UpdateCookingTechnique applies a partial update (PATCH
// /recipes/cooking-techniques/{id}/).
func (c *Client) UpdateCookingTechnique(ctx context.Context, id int, in CookingTechniqueUpdateInput) (CookingTechnique, error) {
	var technique CookingTechnique
	if err := c.send(ctx, http.MethodPatch, fmt.Sprintf("/recipes/cooking-techniques/%d/", id), in, &technique); err != nil {
		return CookingTechnique{}, err
	}
	return technique, nil
}

// DeleteCookingTechnique removes a technique (DELETE
// /recipes/cooking-techniques/{id}/ → 204).
func (c *Client) DeleteCookingTechnique(ctx context.Context, id int) error {
	return c.send(ctx, http.MethodDelete, fmt.Sprintf("/recipes/cooking-techniques/%d/", id), nil, nil)
}
