package prompt

import (
	"fmt"
	"io"
	"os"
	"strings"

	"golang.org/x/term"
)

// TerminalSession is a [Session] over a real terminal. It holds the terminal in
// raw mode for the life of the form, which is what buys line editing, history on
// the arrow keys, and Tab completion.
type TerminalSession struct {
	terminal *term.Terminal
	fd       int
	oldState *term.State
	input    *seedReader
}

// NewTerminalSession puts in into raw mode and draws the form on out. Close
// restores the terminal and has to run — a raw-mode terminal left behind is a
// shell with no echo.
//
// out is separate from in so the prompts land on stderr, leaving stdout for the
// command's data.
func NewTerminalSession(in *os.File, out io.Writer) (*TerminalSession, error) {
	fd := int(in.Fd())
	if !term.IsTerminal(fd) {
		return nil, fmt.Errorf("stdin is not a terminal")
	}
	oldState, err := term.MakeRaw(fd)
	if err != nil {
		return nil, fmt.Errorf("put the terminal into raw mode: %w", err)
	}
	input := &seedReader{src: in}
	terminal := term.NewTerminal(struct {
		io.Reader
		io.Writer
	}{input, out}, "")
	// A pty with no window size reports 0, and a zero-width terminal wraps after
	// every character. NewTerminal's own 80x24 is the better guess.
	if width, height, err := term.GetSize(fd); err == nil && width > 0 && height > 0 {
		_ = terminal.SetSize(width, height)
	}
	return &TerminalSession{terminal: terminal, fd: fd, oldState: oldState, input: input}, nil
}

// Close restores the terminal to the state it was in before the form.
func (s *TerminalSession) Close() error { return term.Restore(s.fd, s.oldState) }

// Write draws form output on the terminal, which rewrites the line endings raw
// mode needs and repaints whatever line is being edited.
func (s *TerminalSession) Write(p []byte) (int, error) { return s.terminal.Write(p) }

// Completes reports that Tab works here.
func (s *TerminalSession) Completes() bool { return true }

// ReadLine asks one question, with seed already on the line and Tab cycling
// choices.
func (s *TerminalSession) ReadLine(label, seed string, choices []string) (string, error) {
	s.terminal.SetPrompt(label)
	s.terminal.AutoCompleteCallback = (&cycler{choices: choices}).complete
	s.input.seed(seed)
	return s.terminal.ReadLine()
}

// seedReader hands the terminal a string as though it had been typed, then goes
// back to reading the keyboard.
//
// This is what puts a rejected answer back on the line: x/term has no call for
// setting the edit buffer, and it cannot tell a seeded byte from a keystroke.
type seedReader struct {
	pending []byte
	src     io.Reader
}

func (r *seedReader) seed(s string) { r.pending = []byte(s) }

func (r *seedReader) Read(p []byte) (int, error) {
	if len(r.pending) > 0 {
		n := copy(p, r.pending)
		r.pending = r.pending[n:]
		return n, nil
	}
	return r.src.Read(p)
}

// cycler completes on Tab by walking the choices that match what has been typed,
// one per press, wrapping at the end.
//
// Cycling beats completing to the common prefix for a closed vocabulary of a
// dozen short words: Tab on an empty line browses the whole list, which is the
// case a prefix completer answers with nothing at all.
type cycler struct {
	choices []string
	base    string
	last    string
	index   int
	active  bool
}

// complete is an x/term AutoCompleteCallback. Any key other than Tab ends the
// current cycle, so typing after a Tab starts the next one from what is on the
// line rather than from where the walk had got to.
func (c *cycler) complete(line string, pos int, key rune) (string, int, bool) {
	if key != '\t' || len(c.choices) == 0 {
		c.active = false
		return "", 0, false
	}
	typed := line[:pos]
	if !c.active || typed != c.last {
		c.base = typed
		c.index = 0
		c.active = true
	}
	matches := matching(c.choices, c.base)
	if len(matches) == 0 {
		c.active = false
		return "", 0, false
	}
	completed := matches[c.index%len(matches)]
	c.index++
	c.last = completed
	return completed + line[pos:], len(completed), true
}

// matching returns the choices containing typed, case-insensitively, with the
// ones it is a prefix of ranked first.
//
// Substring rather than prefix alone, because a choice is often a phrase: a
// project called "Convert theme and font from bash to Go" is found by typing
// "theme", which is how anyone would go looking for it. Prefixes still rank
// ahead, so a vocabulary of single words behaves the way a shell taught
// everyone to expect — "ho" reaches "Home" before it reaches "Chore".
func matching(choices []string, typed string) []string {
	lowered := strings.ToLower(typed)
	var prefixed, contained []string
	for _, choice := range choices {
		switch folded := strings.ToLower(choice); {
		case strings.HasPrefix(folded, lowered):
			prefixed = append(prefixed, choice)
		case strings.Contains(folded, lowered):
			contained = append(contained, choice)
		}
	}
	return append(prefixed, contained...)
}
