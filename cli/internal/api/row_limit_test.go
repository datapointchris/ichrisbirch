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

// Zero is a row count a caller can mean, so it reaches the server as limit=0
// and the API answers with nothing. Omitting it is what asks for every row, and
// only an absent limit does that.
func TestApplyLimit_SendsAnExplicitZero(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	if _, err := client.ListCountdowns(context.Background(), intptr(0)); err != nil {
		t.Fatalf("ListCountdowns: %v", err)
	}
	if *query != "limit=0" {
		t.Errorf("query = %q, want limit=0 so zero rows is what the caller gets", *query)
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
