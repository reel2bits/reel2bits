LDFLAGS += -X "/setting.BuildTime=$(shell date -u '+%Y-%m-%d %I:%M:%S %Z')"
LDFLAGS += -X "/setting.BuildGitHash=$(shell git rev-parse HEAD)"
EXTRA_GOFLAGS ?=

OS := $(shell uname)

ifeq ($(OS), Windows_NT)
	EXECUTABLE := reel2bits.exe
else
	EXECUTABLE := reel2bits
endif

ifneq ($(DRONE_TAG),)
	VERSION ?= $(subst v,,$(DRONE_TAG))
else
	ifneq ($(DRONE_BRANCH),)
		VERSION ?= $(subst release/v,,$(DRONE_BRANCH))
	else
		VERSION ?= master
	endif
endif

DIST := dist

DATA_FILES := $(shell find conf | sed 's/ /\\ /g')

TAGS=sqlite
NOW=$(shell date -u '+%Y%m%d%I%M%S')

GOFMT ?= gofmt -s

GOFILES := $(shell find . -name "*.go" -type f ! -path "./vendor/*" ! -path "*/bindata.go")
PACKAGES ?= $(filter-out dev.sigpipe.me/dashie/reel2bits/integrations,$(shell go list ./... | grep -v /vendor/))

SOURCES ?= $(shell find . -name "*.go" -type f)

.PHONY: build clean

all: build

check: test

web: build
	./reel2bits web

vet:
	go vet $(PACKAGES)

build: $(EXECUTABLE)

$(EXECUTABLE): $(SOURCES)
	go build $(BUILD_FLAGS) $(EXTRA_GOFLAGS) -tags '$(TAGS)' -ldflags '$(LDFLAGS)' -o $@

clean:
	go clean -i ./...
	rm -f integrations.*.test

clean-mac: clean
	find . -name ".DS_Store" -delete

test: fmt-check
	go test -cover -v $(PACKAGES)


required-gofmt-version:
	@go version  | grep -q '\(1.7\|1.8\|1.9\)' || { echo "We require go version 1.7, 1.8 or 1.9 to format code" >&2 && exit 1; }

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

integrations.sqlite.test: $(SOURCES)
	go test -c dev.sigpipe.me/dashie/reel2bits/integrations -o integrations.sqlite.test -tags 'sqlite'

.PHONY: test-sqlite
test-sqlite: integrations.sqlite.test
	APP_ROOT=${CURDIR} APP_CONF=integrations/sqlite.ini ./integrations.sqlite.test

lint:
	@hash golint > /dev/null 2>&1; if [ $$? -ne 0 ]; then \
		go get -u github.com/golang/lint/golint; \
	fi
	for PKG in $(PACKAGES); do golint -set_exit_status $$PKG || exit 1; done;

.PHONY: misspell-check
misspell-check:
	@hash misspell > /dev/null 2>&1; if [ $$? -ne 0 ]; then \
		go get -u github.com/client9/misspell/cmd/misspell; \
	fi
	misspell -error -i unknwon $(GOFILES)

.PHONY: misspell
misspell:
	@hash misspell > /dev/null 2>&1; if [ $$? -ne 0 ]; then \
		go get -u github.com/client9/misspell/cmd/misspell; \
	fi
	misspell -w -i unknwon $(GOFILES)

.PHONY: release
release: release-dirs release-windows release-linux release-darwin release-copy release-check

.PHONY: release-dirs
release-dirs:
	mkdir -p $(DIST)/binaries $(DIST)/release

.PHONY: release-windows
release-windows:
	@hash xgo > /dev/null 2>&1; if [ $$? -ne 0 ]; then \
		go get -u github.com/karalabe/xgo; \
	fi
	xgo -dest $(DIST)/binaries -tags 'netgo $(TAGS)' -ldflags '-linkmode external -extldflags "-static" $(LDFLAGS)' -targets 'windows/*' -out reel2bits-$(VERSION) .
ifeq ($(CI),drone)
	mv /build/* $(DIST)/binaries
endif

.PHONY: release-linux
release-linux:
	@hash xgo > /dev/null 2>&1; if [ $$? -ne 0 ]; then \
		go get -u github.com/karalabe/xgo; \
	fi
	xgo -dest $(DIST)/binaries -tags 'netgo $(TAGS)' -ldflags '-linkmode external -extldflags "-static" $(LDFLAGS)' -targets 'linux/*' -out reel2bits-$(VERSION) .
ifeq ($(CI),drone)
	mv /build/* $(DIST)/binaries
endif

.PHONY: release-darwin
release-darwin:
	@hash xgo > /dev/null 2>&1; if [ $$? -ne 0 ]; then \
		go get -u github.com/karalabe/xgo; \
	fi
	xgo -dest $(DIST)/binaries -tags 'netgo $(TAGS)' -ldflags '$(LDFLAGS)' -targets 'darwin/*' -out reel2bits-$(VERSION) .
ifeq ($(CI),drone)
	mv /build/* $(DIST)/binaries
endif

.PHONY: release-copy
release-copy:
	$(foreach file,$(wildcard $(DIST)/binaries/$(EXECUTABLE)-*),cp $(file) $(DIST)/release/$(notdir $(file));)

.PHONY: release-check
release-check:
	cd $(DIST)/release; $(foreach file,$(wildcard $(DIST)/release/$(EXECUTABLE)-*),sha256sum $(notdir $(file)) > $(notdir $(file)).sha256;)
