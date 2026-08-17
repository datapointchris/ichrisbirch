// Package prompt asks for a record's fields one at a time, on a terminal.
//
// A form is a list of [Field]s. Each is asked in turn; a field with a fixed set
// of values lists them and completes on Tab; a rejected answer comes back in the
// editable buffer instead of being thrown away, so a typo in the last field
// never costs the four already typed.
//
// Nothing here imports the rest of this repo and the only dependency is
// golang.org/x/term, so copying the directory is the whole port to another
// project.
package prompt

import (
	"fmt"
	"io"
	"strings"
	"text/tabwriter"
)

// Session is where a form asks its questions — a writer for everything the form
// says, and a line reader for what it asks. [TerminalSession] is the real one;
// [PlainSession] drives a form from ordinary streams.
type Session interface {
	io.Writer

	// ReadLine writes label and returns the line typed after it. seed is placed
	// in the editable buffer before the first keystroke, which is how a rejected
	// answer comes back for correction rather than being retyped. choices, when
	// non-empty, complete on Tab. A canceled read returns io.EOF.
	ReadLine(label, seed string, choices []string) (string, error)

	// Completes reports whether ReadLine honors choices, so a form only
	// advertises Tab where pressing it does something.
	Completes() bool
}

// Field is one question in a form.
type Field struct {
	// Key names this field's answer in the returned [Answers].
	Key string

	// Label is the word the question is asked with — "Category".
	Label string

	// Hint is one line printed above the first ask, for a constraint the label
	// cannot carry: "Lower is higher priority."
	Hint string

	// Default is taken when the answer is empty, and is shown in the prompt.
	Default string

	// Choices are listed before the first ask and completed on Tab. Listing them
	// is all this does — what the field accepts is Validate's decision.
	Choices []string

	// Optional lets an empty answer through. The field is then absent from
	// [Answers] rather than present and empty.
	Optional bool

	// Validate rejects a bad answer and returns the canonical spelling of a good
	// one, so "chore" can be stored as "Chore". Its error is printed as-is and
	// the answer is offered back for editing, which makes the error text the
	// only place the field explains itself.
	Validate func(string) (string, error)
}

// prompt is the text the answer is typed after. A default is worth showing
// because Enter takes it; "(optional)" is worth showing because Enter skips it.
func (f Field) prompt() string {
	switch {
	case f.Default != "":
		return fmt.Sprintf("%s [%s]: ", f.Label, f.Default)
	case f.Optional:
		return fmt.Sprintf("%s (optional): ", f.Label)
	default:
		return f.Label + ": "
	}
}

// Answers holds one form's answers, keyed by [Field.Key]. A skipped optional
// field is absent rather than present and empty, so a caller can tell "left
// alone" from "set to nothing".
type Answers map[string]string

// Get returns the answer for key, or "" when the field was skipped.
func (a Answers) Get(key string) string { return a[key] }

// Has reports whether key was answered.
func (a Answers) Has(key string) bool {
	_, ok := a[key]
	return ok
}

// Merge copies other's answers in without overwriting anything already present.
// Flags outrank prompts on purpose: a form only ever asks for what the flags
// left out, so anything already here came from the caller.
func (a Answers) Merge(other Answers) {
	for key, value := range other {
		if _, ok := a[key]; !ok {
			a[key] = value
		}
	}
}

// Form is an ordered set of fields asked as one pass.
type Form struct {
	// Intro is printed once, before the first field.
	Intro string

	Fields []Field
}

// Run asks every field in order and returns the answers. Canceling (Ctrl-C,
// Ctrl-D, or a closed stream) returns io.EOF and no answers — a half-filled
// record is not a record.
func (f Form) Run(s Session) (Answers, error) {
	if f.Intro != "" {
		_, _ = fmt.Fprintf(s, "%s\n\n", f.Intro)
	}
	answers := Answers{}
	for _, field := range f.Fields {
		answer, err := ask(s, field)
		if err != nil {
			return nil, err
		}
		if answer != "" {
			answers[field.Key] = answer
		}
	}
	return answers, nil
}

// ask puts one field to the session, re-asking until the answer validates. The
// rejected answer is seeded into the next read, so a typo is corrected in place
// and every field already answered stays answered.
func ask(s Session, field Field) (string, error) {
	if field.Hint != "" {
		_, _ = fmt.Fprintln(s, field.Hint)
	}
	if len(field.Choices) > 0 {
		writeChoices(s, field)
	}
	seed := ""
	for {
		answer, err := s.ReadLine(field.prompt(), seed, field.Choices)
		if err != nil {
			return "", err
		}
		answer = strings.TrimSpace(answer)
		switch {
		case answer != "":
		case field.Default != "":
			answer = field.Default
		case field.Optional:
			return "", nil
		default:
			_, _ = fmt.Fprintf(s, "  %s is required.\n", field.Label)
			seed = ""
			continue
		}
		if field.Validate == nil {
			return answer, nil
		}
		value, err := field.Validate(answer)
		if err != nil {
			_, _ = fmt.Fprintf(s, "  %v\n", err)
			seed = answer
			continue
		}
		return value, nil
	}
}

// choiceColumns is how many choices go on one line.
const choiceColumns = 4

// writeChoices lists what the field accepts, in columns, above the first ask.
func writeChoices(s Session, field Field) {
	_, _ = fmt.Fprintf(s, "%s is one of:\n", field.Label)
	tw := tabwriter.NewWriter(s, 0, 4, 2, ' ', 0)
	for i, choice := range field.Choices {
		if i%choiceColumns == 0 {
			_, _ = fmt.Fprint(tw, "  ")
		}
		_, _ = fmt.Fprintf(tw, "%s\t", choice)
		if (i+1)%choiceColumns == 0 {
			_, _ = fmt.Fprintln(tw)
		}
	}
	if len(field.Choices)%choiceColumns != 0 {
		_, _ = fmt.Fprintln(tw)
	}
	_ = tw.Flush()
	if s.Completes() {
		_, _ = fmt.Fprintln(s, "  Tab cycles the matches.")
	}
}
