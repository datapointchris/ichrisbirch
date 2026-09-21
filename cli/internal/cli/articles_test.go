package cli

import (
	"bytes"
	"strings"
	"testing"
	"time"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
)

// The worker writes the instant in UTC. 03:00 UTC on the 18th is 23:00 on the
// 17th in New York.
func TestPrintBulkImportStatus_APausedBatchSaysWhenItResumes(t *testing.T) {
	original := time.Local
	time.Local = newYork(t)
	t.Cleanup(func() { time.Local = original })
	resumesAt := "2026-09-18T03:00:00+00:00"
	status := api.ArticleBulkImportStatus{BatchID: "batch", Status: "paused", ResumesAt: &resumesAt, Total: 3, Processed: 1}

	var out bytes.Buffer
	printBulkImportStatus(&out, status)

	if !strings.Contains(out.String(), "resumes:   2026-09-17 23:00") {
		t.Errorf("a paused batch does not print when it resumes on this machine's clock:\n%s", out.String())
	}
}

// A batch that is not paused has no ResumesAt. Printing it reaches the nil
// guard, and without the guard the dereference panics and fails this test.
func TestPrintBulkImportStatus_ABatchWithNoResumeTimePrints(t *testing.T) {
	status := api.ArticleBulkImportStatus{BatchID: "batch", Status: "processing", Total: 3, Processed: 1}

	var out bytes.Buffer
	printBulkImportStatus(&out, status)

	if !strings.Contains(out.String(), "batch") {
		t.Errorf("the batch id is missing:\n%s", out.String())
	}
}
