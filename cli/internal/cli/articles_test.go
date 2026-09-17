package cli

import (
	"bytes"
	"strings"
	"testing"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
)

func TestPrintBulkImportStatus_APausedBatchSaysWhenItResumes(t *testing.T) {
	resumesAt := "2026-09-18T03:00:00+00:00"
	status := api.ArticleBulkImportStatus{BatchID: "batch", Status: "paused", ResumesAt: &resumesAt, Total: 3, Processed: 1}

	var out bytes.Buffer
	printBulkImportStatus(&out, status)

	if !strings.Contains(out.String(), "resumes:   "+resumesAt) {
		t.Errorf("a paused batch does not say when it resumes:\n%s", out.String())
	}
}

func TestPrintBulkImportStatus_ARunningBatchHasNoResumeLine(t *testing.T) {
	status := api.ArticleBulkImportStatus{BatchID: "batch", Status: "processing", Total: 3, Processed: 1}

	var out bytes.Buffer
	printBulkImportStatus(&out, status)

	if strings.Contains(out.String(), "resumes:") {
		t.Errorf("a batch that is not paused prints a resume time:\n%s", out.String())
	}
}
