# icb CLI build/install.
#
# icb is the ichrisbirch data front door — a Go/cobra thin REST client over the
# FastAPI, the programmatic surface replacing the MCP. It is a per-machine
# developer tool, not one of the deployed containers, so it installs to $GOBIN
# (defaults to ~/go/bin) like the rest of the Go tooling in this ecosystem.
# `make install` puts `icb` on your PATH; `make build` drops a binary in ./bin
# for local testing without touching the install location.
#
# The bash ops/deploy tool lives at ../cli/icbops — a different concern, a
# different language. This Makefile only builds the resource CLI.

BINARY  := icb
# Version is git-derived (tag if present, else short sha), with -dirty when the
# working tree has uncommitted changes. Overridable: `make build VERSION=1.2.3`.
VERSION ?= $(shell git describe --tags --always --dirty 2>/dev/null || echo dev)
LDFLAGS := -s -w -X ichrisbirch/cli/internal/cli.version=$(VERSION)

# GOBIN is where installs land; surface the resolved path so `make install` can
# tell the user exactly where the binary went.
GOBIN   := $(shell go env GOBIN)
ifeq ($(GOBIN),)
GOBIN   := $(shell go env GOPATH)/bin
endif

.PHONY: build install test lint fmt clean version

## build: compile the binary to ./bin/icb
build:
	go build -ldflags "$(LDFLAGS)" -o bin/$(BINARY) .

## install: build and install icb to $GOBIN (on your PATH)
# Uses `go build -o` rather than `go install`: the module path is
# `ichrisbirch/cli`, so `go install` would name the binary after the path's last
# segment (`cli`), not `icb`. An explicit -o pins both the name and location.
install:
	go build -ldflags "$(LDFLAGS)" -o "$(GOBIN)/$(BINARY)" .
	@echo "installed $(BINARY) $(VERSION) -> $(GOBIN)/$(BINARY)"

## test: run the CLI test suite
test:
	go test ./...

## lint: vet + gofmt check (fails if any file needs formatting)
lint:
	go vet ./...
	@unformatted=$$(gofmt -l .); \
	if [ -n "$$unformatted" ]; then \
		echo "gofmt needed on:"; echo "$$unformatted"; exit 1; \
	fi

## fmt: format all Go files
fmt:
	gofmt -w .

## clean: remove build artifacts
clean:
	rm -rf bin

## version: print the version that would be embedded
version:
	@echo $(VERSION)
