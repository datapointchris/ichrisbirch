package cli

import (
	"bytes"
	"strings"
	"testing"
	"time"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
)

// Each refusal here is decided before the client exists, so it is exit 2 even
// with the API unreachable.
func TestShopping_AUsageRefusalDoesNotWaitOnTheNetwork(t *testing.T) {
	cases := []struct {
		name string
		args []string
	}{
		{"add with no names and no terminal", []string{"shopping", "add", "--no-input"}},
		{"an unknown status", []string{"shopping", "list", "--status", "bought"}},
		{"a list given a positional", []string{"shopping", "list", "costco"}},
		{"check with no names", []string{"shopping", "check"}},
		{"remove with no names", []string{"shopping", "remove"}},
		{"delete with no name", []string{"shopping", "delete"}},
		{"edit with nothing to change", []string{"shopping", "edit", "eggs"}},
		{"edit emptying the name", []string{"shopping", "edit", "eggs", "--name", ""}},
		{"history with a month span", []string{"shopping", "history", "--since", "6mo"}},
		{"history with a negative limit", []string{"shopping", "history", "--limit", "-1"}},
		{"a section move with no neighbor", []string{"shopping", "sections", "move", "costco"}},
		{"a section move with both neighbors", []string{"shopping", "sections", "move", "costco", "--before", "a", "--after", "b"}},
		{"a section created blank", []string{"shopping", "sections", "create", " "}},
		{"a section renamed blank", []string{"shopping", "sections", "rename", "costco", ""}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			unreachableAPI(t)
			if code := runTree(t, tc.args...); code != 2 {
				t.Errorf("exit code = %d, want 2", code)
			}
		})
	}
}

func TestShopping_BareCommandsPrintHelpAndSucceed(t *testing.T) {
	for _, args := range [][]string{{"shopping"}, {"shopping", "sections"}} {
		if code := runTree(t, args...); code != 0 {
			t.Errorf("%v exit code = %d, want 0", args, code)
		}
	}
}

func TestPrintShoppingList_GroupsUnderEachSection(t *testing.T) {
	costco, note := "Costco", "2 dozen"
	items := []api.ShoppingItem{
		{Name: "wood glue", IsNeeded: true},
		{Name: "eggs", SectionName: &costco, Note: &note, IsNeeded: true},
		{Name: "coffee", SectionName: &costco},
	}
	var out bytes.Buffer
	printShoppingList(&out, items, true)

	want := "Unsorted\n" +
		"  wood glue\n" +
		"Costco\n" +
		"  eggs                   2 dozen\n" +
		"  coffee (off the list)\n"
	if out.String() != want {
		t.Errorf("output =\n%q\nwant\n%q", out.String(), want)
	}
}

func TestEmptyShoppingList_SaysWhatWasEmpty(t *testing.T) {
	cases := map[string]api.ShoppingItemFilter{
		"Nothing on the list.":                    {},
		"Nothing on the list in costco.":          {Section: "costco"},
		"Nothing in the catalog is off the list.": {Status: "stocked"},
		"Nothing in the catalog in hardware.":     {Status: "all", Section: "hardware"},
	}
	for want, filter := range cases {
		if got := emptyShoppingList(filter); got != want {
			t.Errorf("emptyShoppingList(%+v) = %q, want %q", filter, got, want)
		}
	}
}

// The API writes the instant in UTC. 15:00 UTC on the 10th is 11:00 in New York.
func TestPrintShoppingHistory_ShowsThePurchaseOnThisMachinesClock(t *testing.T) {
	original := time.Local
	time.Local = newYork(t)
	t.Cleanup(func() { time.Local = original })

	var out bytes.Buffer
	printShoppingHistory(&out, []api.ShoppingPurchase{{ItemName: "eggs", PurchasedTS: "2026-10-10T15:00:00Z"}})

	if !strings.Contains(out.String(), "2026-10-10 11:00  eggs") {
		t.Errorf("output =\n%s\nwant the row at 2026-10-10 11:00", out.String())
	}
}
