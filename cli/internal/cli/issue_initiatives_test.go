package cli

import "testing"

func TestProgressBarShowsAnyStartAndHoldsBackFullUntilNothingIsOpen(t *testing.T) {
	cases := []struct {
		done, open, filled int
	}{
		{0, 0, 0},
		{0, 4, 0},
		{1, 24, 1},
		{4, 3, 6},
		{49, 1, 9},
		{7, 0, 10},
	}
	for _, c := range cases {
		if got := progressFilled(c.done, c.open); got != c.filled {
			t.Errorf("progressFilled(%d done, %d open) = %d, want %d", c.done, c.open, got, c.filled)
		}
	}
}
