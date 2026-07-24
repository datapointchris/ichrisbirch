package api

import (
	"context"
	"fmt"
	"net/http"
	"net/url"
	"strconv"
	"time"
)

// Article mirrors the articles JSON — a saved-reading row with review metadata.
// Nullable fields are pointers; date fields are full datetimes (RFC3339). Only
// the fields the CLI renders are necessarily used, but the whole contract is
// decoded so --json is faithful.
type Article struct {
	ID           int        `json:"id"`
	Title        string     `json:"title"`
	URL          string     `json:"url"`
	Tags         []string   `json:"tags"`
	Summary      string     `json:"summary"`
	Notes        *string    `json:"notes"`
	SaveDate     time.Time  `json:"save_date"`
	LastReadDate *time.Time `json:"last_read_date"`
	ReadCount    int        `json:"read_count"`
	IsFavorite   bool       `json:"is_favorite"`
	IsCurrent    bool       `json:"is_current"`
	IsArchived   bool       `json:"is_archived"`
	ReviewDays   *int       `json:"review_days"`
}

// ArticleCreateFromURLInput is the body for POST /articles/create-from-url/. The
// server fetches the URL and AI-summarizes it to fill title/summary/tags — the
// only create path the CLI exposes, since the raw POST demands a hand-written
// title and summary.
type ArticleCreateFromURLInput struct {
	URL   string  `json:"url"`
	Notes *string `json:"notes,omitempty"`
}

// ArticleUpdateInput is a partial update (PATCH /articles/{id}/): only changed
// fields are sent. Tags omitempty means an empty list is not sent (leaving tags
// as-is). LastReadDate is a datetime string parsed server-side.
type ArticleUpdateInput struct {
	Title        *string  `json:"title,omitempty"`
	Tags         []string `json:"tags,omitempty"`
	Summary      *string  `json:"summary,omitempty"`
	Notes        *string  `json:"notes,omitempty"`
	IsFavorite   *bool    `json:"is_favorite,omitempty"`
	IsCurrent    *bool    `json:"is_current,omitempty"`
	IsArchived   *bool    `json:"is_archived,omitempty"`
	LastReadDate *string  `json:"last_read_date,omitempty"`
	ReadCount    *int     `json:"read_count,omitempty"`
	ReviewDays   *int     `json:"review_days,omitempty"`
}

// ListArticles returns articles ordered by title (GET /articles/). Each of
// favorites/archived/unread, when non-nil, adds a tri-state filter query param
// (favorites=true returns only favorites due for re-read).
func (c *Client) ListArticles(ctx context.Context, favorites, archived, unread *bool) ([]Article, error) {
	var articles []Article
	if err := c.get(ctx, "/articles/"+articleListQuery(favorites, archived, unread), &articles); err != nil {
		return nil, err
	}
	return articles, nil
}

// GetArticle returns a single article (GET /articles/{id}/). Missing is 404.
func (c *Client) GetArticle(ctx context.Context, id int) (Article, error) {
	var article Article
	if err := c.get(ctx, fmt.Sprintf("/articles/%d/", id), &article); err != nil {
		return Article{}, err
	}
	return article, nil
}

// GetCurrentArticle returns the article marked current (GET /articles/current/),
// or nil when none is current — the endpoint responds with JSON null, which
// decodes into a nil pointer rather than an error.
func (c *Client) GetCurrentArticle(ctx context.Context) (*Article, error) {
	var article *Article
	if err := c.get(ctx, "/articles/current/", &article); err != nil {
		return nil, err
	}
	return article, nil
}

// SearchArticles returns articles whose tags match q (GET /articles/search/?q=).
// Comma-separated terms are matched independently (OR).
func (c *Client) SearchArticles(ctx context.Context, q string) ([]Article, error) {
	path := "/articles/search/?" + url.Values{"q": {q}}.Encode()
	var articles []Article
	if err := c.get(ctx, path, &articles); err != nil {
		return nil, err
	}
	return articles, nil
}

// CreateArticleFromURL creates an article by fetching and AI-summarizing a URL
// (POST /articles/create-from-url/). A duplicate URL is a 409.
func (c *Client) CreateArticleFromURL(ctx context.Context, in ArticleCreateFromURLInput) (Article, error) {
	var article Article
	if err := c.send(ctx, http.MethodPost, "/articles/create-from-url/", in, &article); err != nil {
		return Article{}, err
	}
	return article, nil
}

// UpdateArticle applies a partial update (PATCH /articles/{id}/).
func (c *Client) UpdateArticle(ctx context.Context, id int, in ArticleUpdateInput) (Article, error) {
	var article Article
	if err := c.send(ctx, http.MethodPatch, fmt.Sprintf("/articles/%d/", id), in, &article); err != nil {
		return Article{}, err
	}
	return article, nil
}

// DeleteArticle removes an article (DELETE /articles/{id}/ → 204).
func (c *Client) DeleteArticle(ctx context.Context, id int) error {
	return c.send(ctx, http.MethodDelete, fmt.Sprintf("/articles/%d/", id), nil, nil)
}

// articleListQuery renders the tri-state list filters, omitting any that is nil
// so an unset filter sends no param at all.
func articleListQuery(favorites, archived, unread *bool) string {
	params := url.Values{}
	if favorites != nil {
		params.Set("favorites", strconv.FormatBool(*favorites))
	}
	if archived != nil {
		params.Set("archived", strconv.FormatBool(*archived))
	}
	if unread != nil {
		params.Set("unread", strconv.FormatBool(*unread))
	}
	if encoded := params.Encode(); encoded != "" {
		return "?" + encoded
	}
	return ""
}
