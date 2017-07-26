LDFLAGS += -X "/setting.BuildTime=$(shell date -u '+%Y-%m-%d %I:%M:%S %Z')"
LDFLAGS += -X "/setting.BuildGitHash=$(shell git rev-parse HEAD)"

OS := $(shell uname)

DATA_FILES := $(shell find conf | sed 's/ /\\ /g')

BUILD_FLAGS:=-o reel2bits 
TAGS=sqlite
NOW=$(shell date -u '+%Y%m%d%I%M%S')

GOFMT ?= gofmt -s

GOFILES := $(shell find . -name "*.go" -type f ! -path "./vendor/*" ! -path "*/bindata.go")
PACKAGES ?= $(shell go list ./... | grep -v /vendor/)

.PHONY: build clean

all: build

check: test

web: build
	./reel2bits web

vet:
	go vet $(PACKAGES)

build:
	go build $(BUILD_FLAGS) -ldflags '$(LDFLAGS)' -tags '$(TAGS)'

build-dev: govet
	go build $(BUILD_FLAGS) -tags '$(TAGS)'

build-dev-race: govet
	go build $(BUILD_FLAGS) -race -tags '$(TAGS)'

clean:
	go clean -i ./...

clean-mac: clean
	find . -name ".DS_Store" -delete

test:
	go test -cover -race -v $(PACKAGES)


required-gofmt-version:
	@go version  | grep -q '\(1.7\|1.8\)' || { echo "We require go version 1.7 or 1.8 to format code" >&2 && exit 1; }

.PHONY: fmt
fmt: required-gofmt-version
	$(GOFMT) -w $(GOFILES)

.PHONY: fmt-check
fmt-check: required-gofmt-version
	# get all go files and run go fmt on them
	@diff=$$($(GOFMT) -d $(GOFILES)); \
	if [ -n "$$diff" ]; then \
		echo "Please run 'make fmt' and commit the result:"; \
		echo "$${diff}"; \
		exit 1; \
	fi;
