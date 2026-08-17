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
// refuse the same value with the same message, including the list of what would
// have worked.
func OneOf(choices []string) func(string) (string, error) {
	return func(answer string) (string, error) {
		for _, choice := range choices {
			if strings.EqualFold(answer, choice) {
				return choice, nil
			}
		}
		return "", fmt.Errorf("unknown value %q — one of: %s", answer, strings.Join(choices, ", "))
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
