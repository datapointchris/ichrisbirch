package cli

import (
	"encoding/json"
	"io"
)

// encodeJSON writes v as indented JSON — the scripting-friendly output shared by
// every resource command's --json flag.
func encodeJSON(out io.Writer, v any) error {
	enc := json.NewEncoder(out)
	enc.SetIndent("", "  ")
	return enc.Encode(v)
}

// strValue dereferences a nullable string field to its value, or "" when nil.
func strValue(s *string) string {
	if s == nil {
		return ""
	}
	return *s
}

// orNone renders an empty string as "(none)" for list-style detail fields.
func orNone(s string) string {
	if s == "" {
		return "(none)"
	}
	return s
}
