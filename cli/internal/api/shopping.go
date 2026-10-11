package api

import (
	"context"
	"net/http"
	"net/url"
)

// ShoppingSection is a part of the shopping list, such as a store or an aisle.
// Its name is unique ignoring case, so a name addresses it as well as its id.
type ShoppingSection struct {
	ID        string  `json:"id"`
	Name      string  `json:"name"`
	Rank      float64 `json:"rank"`
	CreatedTS string  `json:"created_ts"`
}

// ShoppingItem is a row in the catalog of things ever bought. IsNeeded is
// whether it is on the list now; checking it off clears that and keeps the row,
// with its section and place, for the next time it is added. A nil SectionID is
// Unsorted.
type ShoppingItem struct {
	ID              string  `json:"id"`
	Name            string  `json:"name"`
	Note            *string `json:"note"`
	SectionID       *string `json:"section_id"`
	SectionName     *string `json:"section_name"`
	Rank            float64 `json:"rank"`
	IsNeeded        bool    `json:"is_needed"`
	NeededTS        *string `json:"needed_ts"`
	CreatedTS       string  `json:"created_ts"`
	PurchaseCount   int     `json:"purchase_count"`
	LastPurchasedTS *string `json:"last_purchased_ts"`
}

// ShoppingPurchase is one check-off. It copies the item's name, note and
// section at that moment, so it reads the same after the item is renamed,
// moved or forgotten, when ItemID becomes nil.
type ShoppingPurchase struct {
	ID          string  `json:"id"`
	ItemID      *string `json:"item_id"`
	ItemName    string  `json:"item_name"`
	Note        *string `json:"note"`
	SectionName *string `json:"section_name"`
	PurchasedTS string  `json:"purchased_ts"`
}

// ShoppingItemStatuses are the values ShoppingItemFilter.Status takes: what is
// on the list, what is off it, and the whole catalog.
var ShoppingItemStatuses = []string{"needed", "stocked", "all"}

// ShoppingItemFilter narrows a listing. An empty field is not sent, and the
// server then lists what is needed in every section.
type ShoppingItemFilter struct {
	Status  string
	Section string
	Query   string
}

func (f ShoppingItemFilter) query() url.Values {
	params := url.Values{}
	for name, value := range map[string]string{"status": f.Status, "section": f.Section, "q": f.Query} {
		if value != "" {
			params.Set(name, value)
		}
	}
	return params
}

// ShoppingItemAddInput puts a name on the list (POST /shopping/items). A name
// already in the catalog is listed again rather than created. Section omitted
// keeps a known item where it was; clearing it with mergeClearNulls sends an
// explicit null, which is Unsorted.
type ShoppingItemAddInput struct {
	Name    string  `json:"name"`
	Note    *string `json:"note,omitempty"`
	Section *string `json:"section,omitempty"`
}

// ShoppingItemUpdateInput is a partial update (PATCH /shopping/items/{ref}).
// An empty Note clears it. Section is cleared to Unsorted through
// mergeClearNulls. IsNeeded false takes the item off the list without a
// purchase.
type ShoppingItemUpdateInput struct {
	Name     *string `json:"name,omitempty"`
	Note     *string `json:"note,omitempty"`
	Section  *string `json:"section,omitempty"`
	IsNeeded *bool   `json:"is_needed,omitempty"`
}

// ShoppingSectionMove places a section beside another. Exactly one is set.
type ShoppingSectionMove struct {
	Before *string `json:"before,omitempty"`
	After  *string `json:"after,omitempty"`
}

func shoppingSectionPath(ref string) string {
	return "/shopping/sections/" + url.PathEscape(ref)
}

func shoppingItemPath(ref string) string {
	return "/shopping/items/" + url.PathEscape(ref)
}

// ListShoppingSections returns the sections in list order (GET /shopping/sections).
func (c *Client) ListShoppingSections(ctx context.Context, limit *int) ([]ShoppingSection, error) {
	params := url.Values{}
	applyLimit(params, limit)
	var sections []ShoppingSection
	if err := c.get(ctx, withQuery("/shopping/sections", params), &sections); err != nil {
		return nil, err
	}
	return sections, nil
}

// CreateShoppingSection adds a section at the end of the list. A name taken in
// any case is a 409.
func (c *Client) CreateShoppingSection(ctx context.Context, name string) (ShoppingSection, error) {
	var section ShoppingSection
	body := map[string]string{"name": name}
	if err := c.send(ctx, http.MethodPost, "/shopping/sections", body, &section); err != nil {
		return ShoppingSection{}, err
	}
	return section, nil
}

// RenameShoppingSection renames the section ref names, by id or name.
func (c *Client) RenameShoppingSection(ctx context.Context, ref, name string) (ShoppingSection, error) {
	var section ShoppingSection
	body := map[string]string{"name": name}
	if err := c.send(ctx, http.MethodPatch, shoppingSectionPath(ref), body, &section); err != nil {
		return ShoppingSection{}, err
	}
	return section, nil
}

// MoveShoppingSection places a section before or after another.
func (c *Client) MoveShoppingSection(ctx context.Context, ref string, move ShoppingSectionMove) (ShoppingSection, error) {
	var section ShoppingSection
	if err := c.send(ctx, http.MethodPost, shoppingSectionPath(ref)+"/rank", move, &section); err != nil {
		return ShoppingSection{}, err
	}
	return section, nil
}

// DeleteShoppingSection removes a section. Its items move to Unsorted.
func (c *Client) DeleteShoppingSection(ctx context.Context, ref string) error {
	return c.send(ctx, http.MethodDelete, shoppingSectionPath(ref), nil, nil)
}

// ListShoppingItems returns items in list order, section by section with
// Unsorted first (GET /shopping/items). A Query reorders by name instead.
func (c *Client) ListShoppingItems(ctx context.Context, filter ShoppingItemFilter, limit *int) ([]ShoppingItem, error) {
	params := filter.query()
	applyLimit(params, limit)
	var items []ShoppingItem
	if err := c.get(ctx, withQuery("/shopping/items", params), &items); err != nil {
		return nil, err
	}
	return items, nil
}

// GetShoppingItem returns one catalog item, by id or name.
func (c *Client) GetShoppingItem(ctx context.Context, ref string) (ShoppingItem, error) {
	var item ShoppingItem
	if err := c.get(ctx, shoppingItemPath(ref), &item); err != nil {
		return ShoppingItem{}, err
	}
	return item, nil
}

// AddShoppingItem puts a name on the list. Each field in clear is sent as an
// explicit null.
func (c *Client) AddShoppingItem(ctx context.Context, in ShoppingItemAddInput, clear []string) (ShoppingItem, error) {
	body, err := mergeClearNulls(in, clear)
	if err != nil {
		return ShoppingItem{}, err
	}
	var item ShoppingItem
	if err := c.send(ctx, http.MethodPost, "/shopping/items", body, &item); err != nil {
		return ShoppingItem{}, err
	}
	return item, nil
}

// UpdateShoppingItem applies a partial update. Each field in clear is sent as
// an explicit null.
func (c *Client) UpdateShoppingItem(ctx context.Context, ref string, in ShoppingItemUpdateInput, clear []string) (ShoppingItem, error) {
	body, err := mergeClearNulls(in, clear)
	if err != nil {
		return ShoppingItem{}, err
	}
	var item ShoppingItem
	if err := c.send(ctx, http.MethodPatch, shoppingItemPath(ref), body, &item); err != nil {
		return ShoppingItem{}, err
	}
	return item, nil
}

// DeleteShoppingItem forgets an item. Its purchases keep the name they copied.
func (c *Client) DeleteShoppingItem(ctx context.Context, ref string) error {
	return c.send(ctx, http.MethodDelete, shoppingItemPath(ref), nil, nil)
}

// CheckOffShoppingItem records a purchase and takes the item off the list. An
// item not on the list is a 409.
func (c *Client) CheckOffShoppingItem(ctx context.Context, ref string) (ShoppingPurchase, error) {
	var purchase ShoppingPurchase
	if err := c.send(ctx, http.MethodPost, shoppingItemPath(ref)+"/purchases", nil, &purchase); err != nil {
		return ShoppingPurchase{}, err
	}
	return purchase, nil
}

// ListShoppingPurchases returns the purchase log, newest first (GET
// /shopping/purchases). A nil limit takes the server's default, the newest
// hundred, because the log only grows.
func (c *Client) ListShoppingPurchases(ctx context.Context, start OnOrAfter, end OnOrBefore, zone DayZone, limit *int) ([]ShoppingPurchase, error) {
	params := url.Values{}
	applyDateBounds(params, start, end, zone)
	applyLimit(params, limit)
	var purchases []ShoppingPurchase
	if err := c.get(ctx, withQuery("/shopping/purchases", params), &purchases); err != nil {
		return nil, err
	}
	return purchases, nil
}
