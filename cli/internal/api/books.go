package api

import (
	"context"
	"fmt"
	"net/http"
	"net/url"
)

// Book mirrors the books JSON — a rich catalog row. Nullable fields are pointers.
// The date fields are calendar days ("2006-01-02") and stay strings, because Go's
// time.Time JSON decode requires RFC3339 and rejects a bare date — the same reason
// Countdown.DueDate is a string. Only the fields the CLI renders are necessarily
// used, but the whole contract is decoded so --json is faithful.
type Book struct {
	ID             int      `json:"id"`
	ISBN           *string  `json:"isbn"`
	Title          string   `json:"title"`
	Author         string   `json:"author"`
	Tags           []string `json:"tags"`
	GoodreadsURL   *string  `json:"goodreads_url"`
	Priority       *int     `json:"priority"`
	PurchaseDate   *string  `json:"purchase_date"`
	PurchasePrice  *float64 `json:"purchase_price"`
	SellDate       *string  `json:"sell_date"`
	SellPrice      *float64 `json:"sell_price"`
	ReadStartDate  *string  `json:"read_start_date"`
	ReadFinishDate *string  `json:"read_finish_date"`
	Rating         *int     `json:"rating"`
	Location       *string  `json:"location"`
	Notes          *string  `json:"notes"`
	Ownership      string   `json:"ownership"`
	Progress       string   `json:"progress"`
	RejectReason   *string  `json:"reject_reason"`
	Review         *string  `json:"review"`
}

// BookCreateInput is the body for creating a book. Title, Author, and a non-empty
// Tags list are required by the API; everything else is optional. Date fields are
// strings so the server parses them. Ownership/Progress default server-side.
type BookCreateInput struct {
	Title          string   `json:"title"`
	Author         string   `json:"author"`
	Tags           []string `json:"tags"`
	ISBN           *string  `json:"isbn,omitempty"`
	GoodreadsURL   *string  `json:"goodreads_url,omitempty"`
	Priority       *int     `json:"priority,omitempty"`
	PurchaseDate   *string  `json:"purchase_date,omitempty"`
	PurchasePrice  *float64 `json:"purchase_price,omitempty"`
	SellDate       *string  `json:"sell_date,omitempty"`
	SellPrice      *float64 `json:"sell_price,omitempty"`
	ReadStartDate  *string  `json:"read_start_date,omitempty"`
	ReadFinishDate *string  `json:"read_finish_date,omitempty"`
	Rating         *int     `json:"rating,omitempty"`
	Location       *string  `json:"location,omitempty"`
	Notes          *string  `json:"notes,omitempty"`
	Ownership      *string  `json:"ownership,omitempty"`
	Progress       *string  `json:"progress,omitempty"`
	RejectReason   *string  `json:"reject_reason,omitempty"`
	Review         *string  `json:"review,omitempty"`
}

// BookUpdateInput is a partial update (PATCH /books/{id}/): only changed fields
// are sent. Tags omitempty means an empty list is not sent (leaving tags as-is).
type BookUpdateInput struct {
	Title          *string  `json:"title,omitempty"`
	Author         *string  `json:"author,omitempty"`
	Tags           []string `json:"tags,omitempty"`
	ISBN           *string  `json:"isbn,omitempty"`
	GoodreadsURL   *string  `json:"goodreads_url,omitempty"`
	Priority       *int     `json:"priority,omitempty"`
	PurchaseDate   *string  `json:"purchase_date,omitempty"`
	PurchasePrice  *float64 `json:"purchase_price,omitempty"`
	SellDate       *string  `json:"sell_date,omitempty"`
	SellPrice      *float64 `json:"sell_price,omitempty"`
	ReadStartDate  *string  `json:"read_start_date,omitempty"`
	ReadFinishDate *string  `json:"read_finish_date,omitempty"`
	Rating         *int     `json:"rating,omitempty"`
	Location       *string  `json:"location,omitempty"`
	Notes          *string  `json:"notes,omitempty"`
	Ownership      *string  `json:"ownership,omitempty"`
	Progress       *string  `json:"progress,omitempty"`
	RejectReason   *string  `json:"reject_reason,omitempty"`
	Review         *string  `json:"review,omitempty"`
}

// BookFilter narrows a listing. An empty field is not sent, so the zero value
// lists everything. A struct rather than positional strings because the filters
// are same-typed and a call site reading ListBooks(ctx, "", "reading") cannot
// be checked by eye.
type BookFilter struct {
	Ownership string
	Progress  string
}

func (f BookFilter) query() url.Values {
	params := url.Values{}
	if f.Ownership != "" {
		params.Set("ownership", f.Ownership)
	}
	if f.Progress != "" {
		params.Set("progress", f.Progress)
	}
	return params
}

// ListBooks returns books ordered by priority (GET /books/), narrowed by filter
// and by bounds — a range over when a book was finished. A zero DateBounds
// narrows nothing.
func (c *Client) ListBooks(ctx context.Context, filter BookFilter, bounds DateBounds) ([]Book, error) {
	params := filter.query()
	bounds.apply(params)
	path := withQuery("/books/", params)
	var books []Book
	if err := c.get(ctx, path, &books); err != nil {
		return nil, err
	}
	return books, nil
}

// SearchBooks returns books matching q across title, author, and tags
// (GET /books/search/?q=). Comma-separated terms preserve phrases.
func (c *Client) SearchBooks(ctx context.Context, q string) ([]Book, error) {
	path := "/books/search/?" + url.Values{"q": {q}}.Encode()
	var books []Book
	if err := c.get(ctx, path, &books); err != nil {
		return nil, err
	}
	return books, nil
}

// GetBook returns a single book (GET /books/{id}/). Missing is 404.
func (c *Client) GetBook(ctx context.Context, id int) (Book, error) {
	var book Book
	if err := c.get(ctx, fmt.Sprintf("/books/%d/", id), &book); err != nil {
		return Book{}, err
	}
	return book, nil
}

// GetBookByISBN returns a book by ISBN (GET /books/isbn/{isbn}/). Missing is 404.
func (c *Client) GetBookByISBN(ctx context.Context, isbn string) (Book, error) {
	var book Book
	if err := c.get(ctx, "/books/isbn/"+url.PathEscape(isbn)+"/", &book); err != nil {
		return Book{}, err
	}
	return book, nil
}

// CreateBook creates a book (POST /books/).
func (c *Client) CreateBook(ctx context.Context, in BookCreateInput) (Book, error) {
	var book Book
	if err := c.send(ctx, http.MethodPost, "/books/", in, &book); err != nil {
		return Book{}, err
	}
	return book, nil
}

// UpdateBook applies a partial update (PATCH /books/{id}/).
func (c *Client) UpdateBook(ctx context.Context, id int, in BookUpdateInput) (Book, error) {
	var book Book
	if err := c.send(ctx, http.MethodPatch, fmt.Sprintf("/books/%d/", id), in, &book); err != nil {
		return Book{}, err
	}
	return book, nil
}

// DeleteBook removes a book (DELETE /books/{id}/ → 204).
func (c *Client) DeleteBook(ctx context.Context, id int) error {
	return c.send(ctx, http.MethodDelete, fmt.Sprintf("/books/%d/", id), nil, nil)
}
