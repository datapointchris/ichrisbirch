package cli

import (
	"go/ast"
	"go/parser"
	"go/token"
	"io/fs"
	"path/filepath"
	"strings"
	"testing"
)

// TestNoDefaultStdoutWrites guards the machine contract: `forge brief` parses
// `icb ... --json`, so one stray line on stdout fails the parse as malformed
// JSON rather than as the diagnostic it actually was.
//
// It catches only the writes that pick a stream implicitly — bare fmt.Print*,
// os.Stdout, the print builtins. A diagnostic deliberately handed
// cmd.OutOrStdout() is indistinguishable from data at this level and stays a
// review question; this exists so the accident cannot come back silently.
func TestNoDefaultStdoutWrites(t *testing.T) {
	moduleRoot := "../.."
	fset := token.NewFileSet()

	err := filepath.WalkDir(moduleRoot, func(path string, entry fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if !strings.HasSuffix(path, ".go") || strings.HasSuffix(path, "_test.go") {
			return nil
		}

		file, err := parser.ParseFile(fset, path, nil, 0)
		if err != nil {
			return err
		}

		ast.Inspect(file, func(node ast.Node) bool {
			switch n := node.(type) {
			case *ast.SelectorExpr:
				if pkg, ok := n.X.(*ast.Ident); ok && pkg.Name == "os" && n.Sel.Name == "Stdout" {
					t.Errorf("%s: os.Stdout — data goes to cmd.OutOrStdout(), diagnostics to cmd.ErrOrStderr()",
						fset.Position(n.Pos()))
				}
			case *ast.CallExpr:
				switch fn := n.Fun.(type) {
				case *ast.SelectorExpr:
					pkg, ok := fn.X.(*ast.Ident)
					if ok && pkg.Name == "fmt" && strings.HasPrefix(fn.Sel.Name, "Print") {
						t.Errorf("%s: fmt.%s defaults to stdout — use fmt.Fprint* with an explicit stream",
							fset.Position(n.Pos()), fn.Sel.Name)
					}
				case *ast.Ident:
					if fn.Name == "print" || fn.Name == "println" {
						t.Errorf("%s: the %s builtin writes to stderr unbuffered — use fmt.Fprint* with an explicit stream",
							fset.Position(n.Pos()), fn.Name)
					}
				}
			}
			return true
		})
		return nil
	})
	if err != nil {
		t.Fatalf("walk %s: %v", moduleRoot, err)
	}
}

// TestUsageError_LeavesStdoutClean is the failure this whole rule exists for: a
// caller pipes `icb ... --json` somewhere, gets the invocation wrong, and must
// receive nothing at all on stdout rather than a usage message to parse.
func TestUsageError_LeavesStdoutClean(t *testing.T) {
	for _, args := range [][]string{
		{"nope"},
		{"auth", "nope"},
		{"projects", "--not-a-flag"},
		{"auth", "token", "extra-arg"},
	} {
		t.Run(strings.Join(args, " "), func(t *testing.T) {
			var out, errOut strings.Builder
			root := NewRootCommand()
			root.SetOut(&out)
			root.SetErr(&errOut)
			root.SetArgs(args)

			if code := exitCodeFor(root.Execute()); code != 2 {
				t.Errorf("exit code = %d, want 2 for a usage mistake", code)
			}
			if out.String() != "" {
				t.Errorf("stdout = %q, want empty — a caller parsing stdout must get nothing", out.String())
			}
		})
	}
}
