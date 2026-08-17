package prompt

import (
	"fmt"
	"strconv"
	"strings"
)

// OneOf accepts any of choices, case-insensitively, and returns the choice as
// the list spells it — so "chore" is stored as "Chore".
//
// Share one of these between a command's flag and its prompt. Both doors then
// refuse the same value with the same message, including the part that says
// what would have worked.
//
// What that part can be depends on how many choices there are: a dozen fit in a
// message and eighty do not. So it names the near-misses when the answer has
// any, falls back to the whole list while the list is short, and otherwise says
// how many there were rather than printing them.
func OneOf(choices []string) func(string) (string, error) {
	return func(answer string) (string, error) {
		for _, choice := range choices {
			if strings.EqualFold(answer, choice) {
				return choice, nil
			}
		}
		if near := matching(choices, answer); len(near) > 0 && len(near) <= maxListedChoices {
			return "", fmt.Errorf("unknown value %q — did you mean %s?", answer, strings.Join(near, ", "))
		}
		if len(choices) <= maxListedChoices {
			return "", fmt.Errorf("unknown value %q — one of: %s", answer, strings.Join(choices, ", "))
		}
		return "", fmt.Errorf("unknown value %q — none of the %d known values match", answer, len(choices))
	}
}

// Int accepts a base-10 whole number.
func Int(answer string) (string, error) {
	n, err := strconv.Atoi(answer)
	if err != nil {
		return "", fmt.Errorf("%q is not a whole number", answer)
	}
	return strconv.Itoa(n), nil
}
