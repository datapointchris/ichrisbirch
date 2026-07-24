package cli

import (
	"bufio"
	"fmt"
	"io"
	"strings"
)

// confirm prints prompt and reads a yes/no answer from in. Only "y"/"yes"
// (case-insensitive) approves; EOF or anything else declines. Destructive verbs
// call this unless a --yes flag bypasses it (for non-interactive use).
func confirm(out io.Writer, in io.Reader, prompt string) (bool, error) {
	fmt.Fprintf(out, "%s [y/N] ", prompt)
	line, err := bufio.NewReader(in).ReadString('\n')
	if err != nil && err != io.EOF {
		return false, err
	}
	answer := strings.ToLower(strings.TrimSpace(line))
	return answer == "y" || answer == "yes", nil
}
