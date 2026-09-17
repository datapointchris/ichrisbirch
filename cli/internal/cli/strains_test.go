package cli

import (
	"errors"
	"strings"
	"testing"

	"github.com/spf13/pflag"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
)

// unreachableAPI points the client at a closed port with no stored token, so a
// command that reaches the network fails and one that refuses first does not.
func unreachableAPI(t *testing.T) {
	t.Helper()
	t.Setenv("ICB_API_BASE", "http://127.0.0.1:9")
}

// A bad id is refused by the argument parser, before a client is built, so it
// costs a usage error rather than a network round trip.
func TestStrainsShow_ANonNumericIdIsAUsageError(t *testing.T) {
	if code := runTree(t, "strains", "show", "blue-dream"); code != 2 {
		t.Errorf("exit code = %d, want 2", code)
	}
}

func TestStrainsList_APositionalArgumentIsAUsageError(t *testing.T) {
	if code := runTree(t, "strains", "list", "sativa"); code != 2 {
		t.Errorf("exit code = %d, want 2", code)
	}
}

func TestStrains_BareCommandPrintsHelpAndSucceeds(t *testing.T) {
	if code := runTree(t, "strains"); code != 0 {
		t.Errorf("exit code = %d, want 0", code)
	}
}

// Every refusal that needs no server state is decided before the client exists.
// Deciding them after it turns each one into exit 1 whenever the API is
// unreachable, and a caller that retries on 1 and fixes its arguments on 2
// retries a typo forever.
func TestStrains_AUsageRefusalDoesNotWaitOnTheNetwork(t *testing.T) {
	cases := []struct {
		name string
		args []string
	}{
		{"rating out of range on create", []string{"strains", "create", "--name", "X", "--rating", "11"}},
		{"rating out of range on edit", []string{"strains", "edit", "12", "--rating", "0"}},
		{"missing name with no terminal", []string{"strains", "create", "--no-input"}},
		{"nothing to change", []string{"strains", "edit", "12"}},
		{"emptying a required field on edit", []string{"strains", "edit", "12", "--name", ""}},
		{"emptying a required field on create", []string{"strains", "create", "--name", ""}},
		{"clear beside a value", []string{"strains", "edit", "12", "--rating", "5", "--clear", "rating"}},
		{"unknown clear field", []string{"strains", "edit", "12", "--clear", "nonesuch"}},
		{"a value mixed with an empty one", []string{"strains", "edit", "12", "--effect", "sleepy", "--effect", ""}},
		{"rating floor out of range on list", []string{"strains", "list", "--rating-min", "0"}},
		{"empty filter value on list", []string{"strains", "list", "--effect", ""}},
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

func TestStrainRating_AcceptsTheWholeRange(t *testing.T) {
	for _, answer := range []string{"1", "5", "10"} {
		canonical, err := strainRating(answer)
		if err != nil {
			t.Errorf("strainRating(%s): %v", answer, err)
		}
		if canonical != answer {
			t.Errorf("strainRating(%s) = %q", answer, canonical)
		}
	}
}

// The column's check constraint is 1..10. Asserted on the sentinel rather than
// the sentence, so rewording the message does not fail the test.
func TestStrainRating_RefusesOutsideOneToTen(t *testing.T) {
	for _, answer := range []string{"0", "11", "-1"} {
		_, err := strainRating(answer)
		if !errors.Is(err, errRatingRange) {
			t.Errorf("strainRating(%s) error = %v, want errRatingRange", answer, err)
		}
	}
}

func TestStrainRating_RefusesSomethingThatIsNotANumber(t *testing.T) {
	_, err := strainRating("great")
	if err == nil {
		t.Fatal("strainRating(great) returned no error")
	}
	if errors.Is(err, errRatingRange) {
		t.Error("a non-number is not a range failure")
	}
}

func strainEditFlags(t *testing.T, args ...string) *pflag.FlagSet {
	t.Helper()
	f := pflag.NewFlagSet("test", pflag.ContinueOnError)
	f.String("name", "", "")
	f.String("status", "", "")
	f.String("breeder", "", "")
	f.String("lineage", "", "")
	f.String("type", "", "")
	f.String("source", "", "")
	f.String("notes", "", "")
	f.String("review", "", "")
	f.String("last-tried", "", "")
	f.Int("rating", 0, "")
	f.Float64("thc", 0, "")
	f.Float64("cbd", 0, "")
	f.StringArray("effect", nil, "")
	f.StringArray("flavor", nil, "")
	f.StringArray("terpene", nil, "")
	f.StringArray("tag", nil, "")
	if err := f.Parse(args); err != nil {
		t.Fatalf("Parse: %v", err)
	}
	return f
}

// `""` empties the field, on every field flag that can carry one. A caller
// learns what an empty value does from whichever flag they reach for first and
// uses the next the same way, so one verb answering several ways is a
// disagreement nothing on screen can show.
func TestReadFlagIntent(t *testing.T) {
	cases := []struct {
		name string
		args []string
		flag string
		want flagIntent
	}{
		{"never passed", nil, "breeder", flagUntouched},
		{"a scalar value", []string{"--breeder", "Ken"}, "breeder", flagCarriesValues},
		{"an empty scalar", []string{"--breeder", ""}, "breeder", flagClears},
		{"whitespace is empty", []string{"--breeder", "   "}, "breeder", flagClears},
		{"a list value", []string{"--effect", "sleepy"}, "effect", flagCarriesValues},
		{"an empty list", []string{"--effect", ""}, "effect", flagClears},
		{"a value and an empty one", []string{"--effect", "sleepy", "--effect", ""}, "effect", flagMixesEmptyWithValues},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if got := readFlagIntent(strainEditFlags(t, tc.args...), tc.flag); got != tc.want {
				t.Errorf("readFlagIntent(%s) = %v, want %v", tc.flag, got, tc.want)
			}
		})
	}
}

func TestStrainClears(t *testing.T) {
	t.Run("nothing to clear", func(t *testing.T) {
		got, err := strainClears(strainEditFlags(t), nil)
		if err != nil || len(got) != 0 {
			t.Errorf("got %v, %v; want empty and nil", got, err)
		}
	})

	t.Run("an empty value clears the field it names", func(t *testing.T) {
		got, err := strainClears(strainEditFlags(t, "--breeder", ""), nil)
		if err != nil {
			t.Fatalf("strainClears: %v", err)
		}
		if len(got) != 1 || got[0] != "breeder" {
			t.Errorf("got %v, want [breeder]", got)
		}
	})

	t.Run("an empty repeatable clears the whole list", func(t *testing.T) {
		got, err := strainClears(strainEditFlags(t, "--effect", ""), nil)
		if err != nil {
			t.Fatalf("strainClears: %v", err)
		}
		if len(got) != 1 || got[0] != "effects" {
			t.Errorf("got %v, want [effects]", got)
		}
	})

	t.Run("--clear reaches a numeric field an empty value cannot", func(t *testing.T) {
		got, err := strainClears(strainEditFlags(t), []string{"rating", "thc_percent"})
		if err != nil {
			t.Fatalf("strainClears: %v", err)
		}
		if len(got) != 2 || got[0] != "rating" || got[1] != "thc_percent" {
			t.Errorf("got %v, want [rating thc_percent]", got)
		}
	})

	t.Run("the two required fields refuse to be emptied", func(t *testing.T) {
		for _, name := range []string{"name", "status"} {
			if _, err := strainClears(strainEditFlags(t, "--"+name, ""), nil); err == nil {
				t.Errorf("--%s \"\" was accepted, and the column is NOT NULL", name)
			}
		}
	})

	t.Run("a clear beside its own flag is refused", func(t *testing.T) {
		if _, err := strainClears(strainEditFlags(t, "--rating", "5"), []string{"rating"}); err == nil {
			t.Fatal("got nil, want a refusal")
		}
	})

	t.Run("a clear beside a different flag is fine", func(t *testing.T) {
		if _, err := strainClears(strainEditFlags(t, "--rating", "5"), []string{"effects"}); err != nil {
			t.Errorf("got %v, want nil", err)
		}
	})

	t.Run("an unknown clear field is refused", func(t *testing.T) {
		if _, err := strainClears(strainEditFlags(t), []string{"nonesuch"}); err == nil {
			t.Fatal("got nil, want a refusal")
		}
	})

	t.Run("a value mixed with an empty one is refused", func(t *testing.T) {
		if _, err := strainClears(strainEditFlags(t, "--effect", "sleepy", "--effect", ""), nil); err == nil {
			t.Fatal("got nil, want a refusal")
		}
	})

	t.Run("every clear field maps to a flag the verb registers", func(t *testing.T) {
		edit := findCommand(t, "strains", "edit")
		for field, flagName := range strainClearFields {
			if edit.Flags().Lookup(flagName) == nil {
				t.Errorf("--clear %s maps to --%s, which strains edit does not register", field, flagName)
			}
		}
	})

	t.Run("every clearable flag maps to a field the API names", func(t *testing.T) {
		for flagName, field := range strainClearableFlags {
			if _, known := strainClearFields[field]; !known {
				t.Errorf("--%s empties %q, which --clear does not accept", flagName, field)
			}
		}
	})
}

// A clearing flag reads as untouched in the body, because the clear list is
// what carries it — sending both would say the same thing twice.
func TestListFlag_SeparatesValuesFromClearing(t *testing.T) {
	if got := listFlag(strainEditFlags(t), "effect", nil); got != nil {
		t.Errorf("untouched = %v, want nil", got)
	}
	if got := listFlag(strainEditFlags(t, "--effect", ""), "effect", []string{""}); got != nil {
		t.Errorf("clearing = %v, want nil", got)
	}
	got := listFlag(strainEditFlags(t, "--effect", "sleepy"), "effect", []string{"sleepy"})
	if len(got) != 1 || got[0] != "sleepy" {
		t.Errorf("got %v, want [sleepy]", got)
	}
}

func TestStrainStrFlag_SeparatesValuesFromClearing(t *testing.T) {
	value := "Ken"
	if got := strainStrFlag(strainEditFlags(t), "breeder", &value); got != nil {
		t.Errorf("untouched = %v, want nil", *got)
	}
	empty := ""
	if got := strainStrFlag(strainEditFlags(t, "--breeder", ""), "breeder", &empty); got != nil {
		t.Errorf("clearing = %q, want nil — the clear list carries it", *got)
	}
	if got := strainStrFlag(strainEditFlags(t, "--breeder", "Ken"), "breeder", &value); got == nil || *got != "Ken" {
		t.Errorf("got %v, want Ken", got)
	}
}

func TestIsEmptyStrainUpdate(t *testing.T) {
	if !isEmptyStrainUpdate(api.StrainUpdateInput{}) {
		t.Error("a zero update should read as empty")
	}
	name := "Runtz"
	if isEmptyStrainUpdate(api.StrainUpdateInput{Name: &name}) {
		t.Error("an update with a name should not read as empty")
	}
	if isEmptyStrainUpdate(api.StrainUpdateInput{Effects: []string{"sleepy"}}) {
		t.Error("an update with effects should not read as empty")
	}
}

// Every field the struct carries has to be named, or a flag added later exits 2
// with "nothing to change" while the caller is looking at the value they passed.
func TestIsEmptyStrainUpdate_NamesEveryFieldOnTheStruct(t *testing.T) {
	cases := map[string]api.StrainUpdateInput{
		"Name":          {Name: ptr("x")},
		"Breeder":       {Breeder: ptr("x")},
		"Lineage":       {Lineage: ptr("x")},
		"StrainType":    {StrainType: ptr("x")},
		"Status":        {Status: ptr("x")},
		"THCPercent":    {THCPercent: ptr(1.0)},
		"CBDPercent":    {CBDPercent: ptr(1.0)},
		"Rating":        {Rating: ptr(1)},
		"Effects":       {Effects: []string{"x"}},
		"Flavors":       {Flavors: []string{"x"}},
		"Terpenes":      {Terpenes: []string{"x"}},
		"Tags":          {Tags: []string{"x"}},
		"Source":        {Source: ptr("x")},
		"Notes":         {Notes: ptr("x")},
		"Review":        {Review: ptr("x")},
		"LastTriedDate": {LastTriedDate: ptr("2026-01-01")},
	}
	for field, in := range cases {
		if isEmptyStrainUpdate(in) {
			t.Errorf("%s set, and the update still reads as empty", field)
		}
	}
}

// The help string is registered per verb, because only `create` runs a form and
// `edit` saying it asks would be false.
func TestStrainsCreate_OnlyItSaysNameIsAskedFor(t *testing.T) {
	create := findCommand(t, "strains", "create").Flags().Lookup("name")
	if !strings.Contains(create.Usage, "asked for") {
		t.Errorf("create --name usage = %q, want it to say it is asked for", create.Usage)
	}
	edit := findCommand(t, "strains", "edit").Flags().Lookup("name")
	if strings.Contains(edit.Usage, "asked for") {
		t.Errorf("edit --name usage = %q, and edit never asks", edit.Usage)
	}
}

func TestPrintStrainsTable_AnEmptyResultNamesTheFiltersThatNarrowedIt(t *testing.T) {
	var out strings.Builder
	printStrainsTable(&out, nil, api.StrainFilter{Effect: "giggly", Status: "tried"})
	got := out.String()
	for _, want := range []string{"--effect giggly", "--status tried"} {
		if !strings.Contains(got, want) {
			t.Errorf("empty state = %q, want it to name %s", got, want)
		}
	}
}

func TestPrintStrainsTable_AnUnfilteredEmptyResultSaysSoPlainly(t *testing.T) {
	var out strings.Builder
	printStrainsTable(&out, nil, api.StrainFilter{})
	if got := strings.TrimSpace(out.String()); got != "No strains." {
		t.Errorf("empty state = %q, want %q", got, "No strains.")
	}
}
