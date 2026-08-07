package cli

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/spf13/cobra"
)

// repoFlagCommand builds a bare command carrying just --repo, so the flag
// plumbing is testable without standing up an API client.
func repoFlagCommand() *cobra.Command {
	var repo string
	cmd := &cobra.Command{Use: "test", RunE: func(*cobra.Command, []string) error { return nil }}
	cmd.Flags().StringVar(&repo, "repo", "", "")
	return cmd
}

func TestRepoFlagValue_AbsentIsNoFilter(t *testing.T) {
	cmd := repoFlagCommand()
	if err := cmd.ParseFlags(nil); err != nil {
		t.Fatalf("ParseFlags: %v", err)
	}
	if got := repoFlagValue(cmd, ""); got != nil {
		t.Errorf("repoFlagValue = %v, want nil — an unset flag must not filter", got)
	}
}

func TestRepoFlagValue_EmptyIsTheUntaggedQuestion(t *testing.T) {
	cmd := repoFlagCommand()
	if err := cmd.ParseFlags([]string{"--repo", ""}); err != nil {
		t.Fatalf("ParseFlags: %v", err)
	}
	got := repoFlagValue(cmd, "")
	if got == nil || *got != "" {
		t.Errorf("repoFlagValue = %v, want a pointer to \"\" — --repo \"\" asks for untagged work", got)
	}
}

func TestRepoFlagValue_NamePassesThrough(t *testing.T) {
	cmd := repoFlagCommand()
	if err := cmd.ParseFlags([]string{"--repo", "dotfiles"}); err != nil {
		t.Fatalf("ParseFlags: %v", err)
	}
	got := repoFlagValue(cmd, "dotfiles")
	if got == nil || *got != "dotfiles" {
		t.Errorf("repoFlagValue = %v, want dotfiles", got)
	}
}

// withRegistry points XDG_DATA_HOME at a temp tree holding a registry at the
// path DefaultPath() resolves to, so the tests exercise the real resolution
// rather than an override that only exists for them.
func withRegistry(t *testing.T, body string) {
	t.Helper()
	data := t.TempDir()
	dir := filepath.Join(data, "icb")
	if err := os.MkdirAll(dir, 0o700); err != nil {
		t.Fatalf("creating registry dir: %v", err)
	}
	if err := os.WriteFile(filepath.Join(dir, "repos.json"), []byte(body), 0o600); err != nil {
		t.Fatalf("writing registry: %v", err)
	}
	t.Setenv("XDG_DATA_HOME", data)
}

func TestValidateRepoFlag_RejectsAnUnregisteredRepo(t *testing.T) {
	withRegistry(t, `{"repos":[{"name":"dotfiles"},{"name":"todoui"}]}`)
	cmd := repoFlagCommand()
	if err := cmd.ParseFlags([]string{"--repo", "dotfile"}); err != nil {
		t.Fatalf("ParseFlags: %v", err)
	}
	err := validateRepoFlag(cmd, "dotfile")
	if err == nil {
		t.Fatal("a typo'd repo must be rejected at the moment it is typed")
	}
	if !strings.Contains(err.Error(), "dotfiles") {
		t.Errorf("expected the near-match in the message, got %q", err)
	}
}

func TestValidateRepoFlag_AcceptsARegisteredRepo(t *testing.T) {
	withRegistry(t, `{"repos":[{"name":"dotfiles"}]}`)
	cmd := repoFlagCommand()
	if err := cmd.ParseFlags([]string{"--repo", "dotfiles"}); err != nil {
		t.Fatalf("ParseFlags: %v", err)
	}
	if err := validateRepoFlag(cmd, "dotfiles"); err != nil {
		t.Errorf("validateRepoFlag = %v, want nil", err)
	}
}

// `--repo ""` is how an item is unlinked from its repo, so it must survive
// validation rather than being read as an unknown name.
func TestValidateRepoFlag_EmptyUnlinksRatherThanFailing(t *testing.T) {
	withRegistry(t, `{"repos":[{"name":"dotfiles"}]}`)
	cmd := repoFlagCommand()
	if err := cmd.ParseFlags([]string{"--repo", ""}); err != nil {
		t.Fatalf("ParseFlags: %v", err)
	}
	if err := validateRepoFlag(cmd, ""); err != nil {
		t.Errorf("validateRepoFlag = %v, want nil", err)
	}
}

func TestValidateRepoFlag_UnsetIsNotValidated(t *testing.T) {
	withRegistry(t, `{"repos":[{"name":"dotfiles"}]}`)
	cmd := repoFlagCommand()
	if err := cmd.ParseFlags(nil); err != nil {
		t.Fatalf("ParseFlags: %v", err)
	}
	if err := validateRepoFlag(cmd, ""); err != nil {
		t.Errorf("validateRepoFlag = %v, want nil for an unset flag", err)
	}
}
