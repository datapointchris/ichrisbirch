package cli

import (
	"strings"
	"testing"

	"github.com/spf13/pflag"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
)

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

// The column's check constraint is 1..10, and refusing here says so before the
// round trip rather than after a 422.
func TestStrainRating_RefusesOutsideOneToTen(t *testing.T) {
	for _, answer := range []string{"0", "11", "-1"} {
		if _, err := strainRating(answer); err == nil {
			t.Errorf("strainRating(%s) returned no error", answer)
		}
	}
}

func TestStrainRating_RefusesSomethingThatIsNotANumber(t *testing.T) {
	_, err := strainRating("great")
	if err == nil {
		t.Fatal("strainRating(great) returned no error")
	}
	if !strings.Contains(err.Error(), "whole number") {
		t.Errorf("error = %q, want it to say what a rating is", err)
	}
}

// listFlag resolves the three states an update has to tell apart. The middle
// one is the reason the clear is its own flag: pflag cannot distinguish an
// empty repeatable flag from one never passed.
func TestListFlag_ResolvesLeaveAloneReplaceAndClear(t *testing.T) {
	newFlags := func() *pflag.FlagSet {
		f := pflag.NewFlagSet("test", pflag.ContinueOnError)
		f.StringArray("effect", nil, "")
		f.Bool("clear-effects", false, "")
		return f
	}

	t.Run("untouched is nil, so the column keeps what it holds", func(t *testing.T) {
		f := newFlags()
		if got := listFlag(f, "effect", "clear-effects", nil); got != nil {
			t.Errorf("got %v, want nil", *got)
		}
	})

	t.Run("values replace the list", func(t *testing.T) {
		f := newFlags()
		if err := f.Parse([]string{"--effect", "sleepy"}); err != nil {
			t.Fatalf("Parse: %v", err)
		}
		got := listFlag(f, "effect", "clear-effects", []string{"sleepy"})
		if got == nil || len(*got) != 1 || (*got)[0] != "sleepy" {
			t.Errorf("got %v, want [sleepy]", got)
		}
	})

	t.Run("the clear flag empties it", func(t *testing.T) {
		f := newFlags()
		if err := f.Parse([]string{"--clear-effects"}); err != nil {
			t.Fatalf("Parse: %v", err)
		}
		got := listFlag(f, "effect", "clear-effects", nil)
		if got == nil {
			t.Fatal("got nil, want a pointer to an empty slice")
		}
		if len(*got) != 0 {
			t.Errorf("got %v, want []", *got)
		}
	})

	t.Run("the clear flag wins over values", func(t *testing.T) {
		f := newFlags()
		if err := f.Parse([]string{"--effect", "sleepy", "--clear-effects"}); err != nil {
			t.Fatalf("Parse: %v", err)
		}
		got := listFlag(f, "effect", "clear-effects", []string{"sleepy"})
		if got == nil || len(*got) != 0 {
			t.Errorf("got %v, want []", got)
		}
	})
}

func TestIsEmptyStrainUpdate(t *testing.T) {
	if !isEmptyStrainUpdate(api.StrainUpdateInput{}) {
		t.Error("a zero update should read as empty")
	}
	name := "Runtz"
	if isEmptyStrainUpdate(api.StrainUpdateInput{Name: &name}) {
		t.Error("an update with a name should not read as empty")
	}
	// A cleared array is a change, and reading it as "nothing to change" would
	// refuse the one command that empties a list.
	if isEmptyStrainUpdate(api.StrainUpdateInput{Effects: &[]string{}}) {
		t.Error("clearing an array is a change")
	}
}
