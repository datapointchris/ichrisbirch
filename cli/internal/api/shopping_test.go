package api

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
)

// shoppingRequest is what one call put on the wire.
type shoppingRequest struct {
	method string
	path   string
	query  string
	body   map[string]any
}

// shoppingServer answers every request with reply and records it.
func shoppingServer(t *testing.T, reply string) (*Client, *shoppingRequest) {
	t.Helper()
	got := &shoppingRequest{}
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		got.method, got.path, got.query = r.Method, r.URL.EscapedPath(), r.URL.RawQuery
		raw, _ := io.ReadAll(r.Body)
		if len(raw) > 0 {
			_ = json.Unmarshal(raw, &got.body)
		}
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(reply))
	}))
	t.Cleanup(srv.Close)
	return New(srv.URL, staticTokenClient("t")), got
}

const shoppingItemJSON = `{"id":"0192","name":"wood glue","note":null,"section_id":null,"section_name":null,` +
	`"rank":1,"is_needed":true,"needed_ts":null,"created_ts":"2026-10-10T00:00:00Z","purchase_count":0,"last_purchased_ts":null}`

func TestShoppingItemFilter_QueryOmitsEmptyFields(t *testing.T) {
	cases := []struct {
		name   string
		filter ShoppingItemFilter
		limit  *int
		want   string
	}{
		{"zero value sends nothing", ShoppingItemFilter{}, nil, ""},
		{"every field", ShoppingItemFilter{Status: "all", Section: "Costco", Query: "egg"}, nil, "q=egg&section=Costco&status=all"},
		{"limit zero survives", ShoppingItemFilter{}, intPtr(0), "limit=0"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			client, got := shoppingServer(t, `[]`)
			if _, err := client.ListShoppingItems(context.Background(), tc.filter, tc.limit); err != nil {
				t.Fatalf("ListShoppingItems: %v", err)
			}
			if got.query != tc.want {
				t.Errorf("query = %q, want %q", got.query, tc.want)
			}
		})
	}
}

// Section absent keeps a known item where it was; section null puts it in
// Unsorted. The two are different requests, so the body has to tell them apart.
func TestAddShoppingItem_SectionAbsentAndSectionNullDiffer(t *testing.T) {
	client, got := shoppingServer(t, shoppingItemJSON)
	if _, err := client.AddShoppingItem(context.Background(), ShoppingItemAddInput{Name: "wood glue"}, nil); err != nil {
		t.Fatalf("AddShoppingItem: %v", err)
	}
	if _, present := got.body["section"]; present {
		t.Errorf("body = %v, want no section key", got.body)
	}

	if _, err := client.AddShoppingItem(context.Background(), ShoppingItemAddInput{Name: "wood glue"}, []string{"section"}); err != nil {
		t.Fatalf("AddShoppingItem: %v", err)
	}
	section, present := got.body["section"]
	if !present || section != nil {
		t.Errorf("body = %v, want section: null", got.body)
	}
}

func TestShoppingItemPaths_EscapeAName(t *testing.T) {
	client, got := shoppingServer(t, shoppingItemJSON)
	off := false
	if _, err := client.UpdateShoppingItem(context.Background(), "wood glue", ShoppingItemUpdateInput{IsNeeded: &off}, nil); err != nil {
		t.Fatalf("UpdateShoppingItem: %v", err)
	}
	if got.method != http.MethodPatch || got.path != "/api/v1/shopping/items/wood%20glue" {
		t.Errorf("request = %s %s", got.method, got.path)
	}
	if len(got.body) != 1 || got.body["is_needed"] != false {
		t.Errorf("body = %v, want only is_needed: false", got.body)
	}
}

func TestCheckOffShoppingItem_PostsAPurchase(t *testing.T) {
	client, got := shoppingServer(t, `{"id":"p1","item_id":"0192","item_name":"eggs","note":null,"section_name":null,"purchased_ts":"2026-10-10T15:00:00Z"}`)
	purchase, err := client.CheckOffShoppingItem(context.Background(), "eggs")
	if err != nil {
		t.Fatalf("CheckOffShoppingItem: %v", err)
	}
	if got.method != http.MethodPost || got.path != "/api/v1/shopping/items/eggs/purchases" {
		t.Errorf("request = %s %s", got.method, got.path)
	}
	if purchase.ItemName != "eggs" {
		t.Errorf("purchase = %+v", purchase)
	}
}

func TestListShoppingPurchases_SendsBoundsZoneAndLimit(t *testing.T) {
	client, got := shoppingServer(t, `[]`)
	_, err := client.ListShoppingPurchases(context.Background(), "2026-10-01", "2026-10-31", "America/New_York", intPtr(5))
	if err != nil {
		t.Fatalf("ListShoppingPurchases: %v", err)
	}
	want := "end_date=2026-10-31&limit=5&start_date=2026-10-01&timezone=America%2FNew_York"
	if got.query != want {
		t.Errorf("query = %q, want %q", got.query, want)
	}
}

func TestMoveShoppingSection_SendsOneNeighbor(t *testing.T) {
	client, got := shoppingServer(t, `{"id":"s1","name":"Hardware","rank":2.5,"created_ts":"2026-10-10T00:00:00Z"}`)
	if _, err := client.MoveShoppingSection(context.Background(), "hardware", ShoppingSectionMove{After: strPtr("costco")}); err != nil {
		t.Fatalf("MoveShoppingSection: %v", err)
	}
	if got.path != "/api/v1/shopping/sections/hardware/rank" {
		t.Errorf("path = %s", got.path)
	}
	if len(got.body) != 1 || got.body["after"] != "costco" {
		t.Errorf("body = %v, want only after: costco", got.body)
	}
}
