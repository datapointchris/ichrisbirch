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

	// Choices are listed before the first ask and cycled on Tab. A list too long
	// to read is summarized instead, since scrolling one is the hunt the form
	// exists to end. Listing is all this does — what the field accepts is
	// Validate's decision.
	Choices []string

	// Optional lets an empty answer through. The field is then absent from
	// [Answers] rather than present and empty.
	Optional bool

	// Repeat asks again after every answer and keeps them all, in order, until
	// an empty one ends the run. A repeating field that is not Optional still
	// needs its first answer.
	Repeat bool

	// Multiline reads until a blank line and joins what it read with newlines,
	// for a field carrying prose rather than a value. Choices, Default, and
	// Validate do not apply.
	Multiline bool

	// Validate rejects a bad answer and returns the canonical spelling of a good
	// one, so "chore" can be stored as "Chore". Its error is printed as-is and
	// the answer is offered back for editing, which makes the error text the
	// only place the field explains itself.
	Validate func(string) (string, error)
}

// prompt is the text the answer is typed after. collected is how many answers
// the field already holds, which only a repeating field ever has.
//
// A default is worth showing because Enter takes it; "(optional)" is worth
// showing because Enter skips it; and on a repeating field Enter does a third
// thing, so it says which.
func (f Field) prompt(collected int) string {
	switch {
	case collected > 0:
		return fmt.Sprintf("%s (another, or Enter to move on): ", f.Label)
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
//
// Every key carries a list because a repeating field and a repeatable flag both
// produce several values. Get returns the first, which is the whole story for
// every field that does not repeat.
type Answers map[string][]string

// Get returns the first answer for key, or "" when the field was skipped.
func (a Answers) Get(key string) string {
	if values := a[key]; len(values) > 0 {
		return values[0]
	}
	return ""
}

// All returns every answer for key, in the order they were given.
func (a Answers) All(key string) []string { return a[key] }

// Has reports whether key was answered.
func (a Answers) Has(key string) bool { return len(a[key]) > 0 }

// Merge copies other's answers in without overwriting anything already present.
// Flags outrank prompts on purpose: a form only ever asks for what the flags
// left out, so anything already here came from the caller.
func (a Answers) Merge(other Answers) {
	for key, values := range other {
		if !a.Has(key) {
			a[key] = values
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
		values, err := ask(s, field)
		if err != nil {
			return nil, err
		}
		if len(values) > 0 {
			answers[field.Key] = values
		}
	}
	return answers, nil
}

// ask puts one field to the session and returns everything it collected — one
// value for an ordinary field, several for a repeating one, none for a skipped
// optional one.
func ask(s Session, field Field) ([]string, error) {
	if field.Hint != "" {
		_, _ = fmt.Fprintln(s, field.Hint)
	}
	if len(field.Choices) > 0 {
		writeChoices(s, field)
	}
	if field.Multiline {
		return askProse(s, field)
	}
	var values []string
	for {
		value, err := askValue(s, field, len(values))
		if err != nil {
			return nil, err
		}
		if value == "" {
			return values, nil
		}
		values = append(values, value)
		if !field.Repeat {
			return values, nil
		}
	}
}

// askValue reads one answer, re-asking until it validates. The rejected answer
// is seeded into the next read, so a typo is corrected in place and every field
// already answered stays answered.
//
// collected is how many answers the field already holds. It is what makes an
// empty line mean "no more" on a repeating field that has one, and "you have to
// answer this" on a required field that has none.
func askValue(s Session, field Field, collected int) (string, error) {
	seed := ""
	for {
		answer, err := s.ReadLine(field.prompt(collected), seed, field.Choices)
		if err != nil {
			return "", err
		}
		answer = strings.TrimSpace(answer)
		switch {
		case answer != "":
		case field.Default != "" && collected == 0:
			answer = field.Default
		case field.Optional || collected > 0:
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

// proseGutter marks the lines of a multiline field, so it is clear which ones
// are being collected and that Enter on an empty one ends the field rather than
// the form.
const proseGutter = "  > "

// askProse reads lines until a blank one ends the field, and returns them joined.
func askProse(s Session, field Field) ([]string, error) {
	for {
		_, _ = fmt.Fprintf(s, "%s — one or more lines, blank line ends it:\n", field.Label)
		var lines []string
		for {
			line, err := s.ReadLine(proseGutter, "", nil)
			if err != nil {
				return nil, err
			}
			if strings.TrimSpace(line) == "" {
				break
			}
			lines = append(lines, line)
		}
		if len(lines) > 0 {
			return []string{strings.Join(lines, "\n")}, nil
		}
		if field.Optional {
			return nil, nil
		}
		_, _ = fmt.Fprintf(s, "  %s is required.\n", field.Label)
	}
}

// choiceColumns is how many choices go on one line.
const choiceColumns = 4

// maxListedChoices is where a list stops being a glance and becomes a scroll —
// six rows of four. Past it the field says how many there are instead, because
// printing eighty repo names is the hunt through --help this exists to end.
const maxListedChoices = 24

// writeChoices says what the field accepts, above the first ask.
func writeChoices(s Session, field Field) {
	if len(field.Choices) > maxListedChoices {
		writeChoiceCount(s, field)
		return
	}
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

// writeChoiceCount stands in for a list too long to read. Tab is the whole
// affordance then, so a session without it gets the count and nothing else.
func writeChoiceCount(s Session, field Field) {
	if s.Completes() {
		_, _ = fmt.Fprintf(s, "%s — %d to choose from; type any part of one and Tab cycles the matches.\n",
			field.Label, len(field.Choices))
		return
	}
	_, _ = fmt.Fprintf(s, "%s — %d to choose from.\n", field.Label, len(field.Choices))
}
