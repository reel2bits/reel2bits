# LDFLAGS += -X "/setting.BuildTime=$(shell date -u '+%Y-%m-%d %I:%M:%S %Z')"
# LDFLAGS += -X "/setting.BuildGitHash=$(shell git rev-parse HEAD)"

OS := $(shell uname)

DATA_FILES := $(shell find conf | sed 's/ /\\ /g')

BUILD_FLAGS:=-o reel2bits 
TAGS=sqlite
NOW=$(shell date -u '+%Y%m%d%I%M%S')
GOVET=go tool vet -composites=false -methods=false -structtags=false

.PHONY: build clean

all: build

check: test

web: build
	./reel2bits web

govet:
	$(GOVET) reel2bits.go

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
	go test -cover -race ./...

