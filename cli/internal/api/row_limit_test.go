package api

import (
	"context"
	"testing"
)

func intptr(n int) *int { return &n }

func TestApplyLimit_SendsThePositiveCap(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	if _, err := client.ListCountdowns(context.Background(), intptr(5)); err != nil {
		t.Fatalf("ListCountdowns: %v", err)
	}
	if *query != "limit=5" {
		t.Errorf("query = %q, want limit=5", *query)
	}
}

func TestApplyLimit_OmitsAnAbsentCap(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	if _, err := client.ListCountdowns(context.Background(), nil); err != nil {
		t.Fatalf("ListCountdowns: %v", err)
	}
	if *query != "" {
		t.Errorf("query = %q, want no parameters at all", *query)
	}
}

// Zero means "no cap", so it has to reach the server as an absent parameter. A
// bare limit=0 is a LIMIT 0 against any API that has not adopted the sentinel,
// which answers with nothing — the opposite of what the caller asked for.
func TestApplyLimit_SendsNothingForZero(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	if _, err := client.ListCountdowns(context.Background(), intptr(0)); err != nil {
		t.Fatalf("ListCountdowns: %v", err)
	}
	if *query != "" {
		t.Errorf("query = %q, want limit omitted so zero means every row", *query)
	}
}

func TestApplyLimit_SendsNothingForANegativeCap(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	if _, err := client.ListCountdowns(context.Background(), intptr(-3)); err != nil {
		t.Fatalf("ListCountdowns: %v", err)
	}
	if *query != "" {
		t.Errorf("query = %q, want limit omitted rather than sent as a negative", *query)
	}
}

// Every list read reaches the same helper, so the cap is spelled one way across
// the client rather than once per resource.
func TestApplyLimit_RidesEveryListRead(t *testing.T) {
	ctx := context.Background()
	calls := map[string]func(*Client) error{
		"ListArticles": func(c *Client) error {
			_, err := c.ListArticles(ctx, nil, nil, nil, DateBounds{}, intptr(3))
			return err
		},
		"ListAutoTasks": func(c *Client) error {
			_, err := c.ListAutoTasks(ctx, intptr(3))
			return err
		},
		"ListBooks": func(c *Client) error {
			_, err := c.ListBooks(ctx, BookFilter{}, DateBounds{}, intptr(3))
			return err
		},
		"ListCookingTechniques": func(c *Client) error {
			_, err := c.ListCookingTechniques(ctx, nil, nil, intptr(3))
			return err
		},
		"ListCountdowns": func(c *Client) error {
			_, err := c.ListCountdowns(ctx, intptr(3))
			return err
		},
		"ListEvents": func(c *Client) error {
			_, err := c.ListEvents(ctx, intptr(3))
			return err
		},
		"ListItems": func(c *Client) error {
			_, err := c.ListItems(ctx, nil, "", DateBounds{}, intptr(3))
			return err
		},
		"ListProjectItems": func(c *Client) error {
			_, err := c.ListProjectItems(ctx, "018f-a", "", DateBounds{}, intptr(3))
			return err
		},
		"ListProjects": func(c *Client) error {
			_, err := c.ListProjects(ctx, nil, "", intptr(3))
			return err
		},
		"ListRecipes": func(c *Client) error {
			_, err := c.ListRecipes(ctx, nil, nil, nil, nil, nil, intptr(3))
			return err
		},
	}
	for name, call := range calls {
		t.Run(name, func(t *testing.T) {
			client, query := recordQuery(t, `[]`)
			if err := call(client); err != nil {
				t.Fatalf("%s: %v", name, err)
			}
			if !hasParam(*query, "limit=3") {
				t.Errorf("%s query = %q, want it to carry limit=3", name, *query)
			}
		})
	}
}

// hasParam reports whether an encoded query string carries the given pair. The
// other filters each read supports mean the pair is rarely the whole string.
func hasParam(query, pair string) bool {
	for _, part := range splitQuery(query) {
		if part == pair {
			return true
		}
	}
	return false
}

func splitQuery(query string) []string {
	var parts []string
	start := 0
	for i := range len(query) {
		if query[i] == '&' {
			parts = append(parts, query[start:i])
			start = i + 1
		}
	}
	return append(parts, query[start:])
}
