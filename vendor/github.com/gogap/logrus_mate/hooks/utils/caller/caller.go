package caller

import (
	"runtime"
	"strings"
)

// getCaller returns the filename and the line info of a function
// further down in the call stack.  Passing 0 in as callDepth would
// return info on the function calling getCallerIgnoringLog, 1 the
// parent function, and so on.  Any suffixes passed to getCaller are
// path fragments like "/pkg/log/log.go", and functions in the call
// stack from that file are ignored.
func GetCaller(callDepth int, suffixesToIgnore ...string) (file string, line int) {
	// bump by 1 to ignore the getCaller (this) stackframe
	callDepth++
outer:
	for {
		var ok bool
		_, file, line, ok = runtime.Caller(callDepth)
		if !ok {
			file = "???"
			line = 0
			break
		}

		for _, s := range suffixesToIgnore {
			if strings.HasSuffix(file, s) {
				callDepth++
				continue outer
			}
		}
		break
	}
	return
}

func GetCallerIgnoringLogMulti(callDepth int) (string, int) {
	// the +1 is to ignore this (GetCallerIgnoringLogMulti) frame
	return GetCaller(callDepth+1, "logrus/hooks.go", "logrus/entry.go", "logrus/logger.go", "logrus/exported.go", "proc.go", "asm_amd64.s")
}
