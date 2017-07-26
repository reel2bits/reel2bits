// Copyright 2017 The Gogs Authors. All rights reserved.
// Use of this source code is governed by a MIT-style
// license that can be found in the LICENSE file.

package tool

import (
	"fmt"
	"github.com/rakyll/magicmime"
	"math"
)

// Sizes definitions
const (
	Byte  = 1
	KByte = Byte * 1024
	MByte = KByte * 1024
	GByte = MByte * 1024
	TByte = GByte * 1024
	PByte = TByte * 1024
	EByte = PByte * 1024
)

const rawContentCheckSize = 5000

var bytesSizeTable = map[string]uint64{
	"b":  Byte,
	"kb": KByte,
	"mb": MByte,
	"gb": GByte,
	"tb": TByte,
	"pb": PByte,
	"eb": EByte,
}

func logn(n, b float64) float64 {
	return math.Log(n) / math.Log(b)
}

func humanateBytes(s uint64, base float64, sizes []string) string {
	if s < 10 {
		return fmt.Sprintf("%d B", s)
	}
	e := math.Floor(logn(float64(s), base))
	suffix := sizes[int(e)]
	val := float64(s) / math.Pow(base, math.Floor(e))
	f := "%.0f"
	if val < 10 {
		f = "%.1f"
	}

	return fmt.Sprintf(f+" %s", val, suffix)
}

// FileSize calculates the file size and generate user-friendly string.
func FileSize(s int64) string {
	sizes := []string{"B", "KB", "MB", "GB", "TB", "PB", "EB"}
	return humanateBytes(uint64(s), 1024, sizes)
}

// GetBlobMimeType get mimetype of determined blob
func GetBlobMimeType(blob []byte) (string, error) {
	err := magicmime.Open(magicmime.MAGIC_MIME_TYPE | magicmime.MAGIC_ERROR)
	if err != nil {
		return "", fmt.Errorf("Cannot open magicmime library: %s", err)
	}
	defer magicmime.Close()

	if len(blob) > rawContentCheckSize {
		return magicmime.TypeByBuffer(blob[:rawContentCheckSize])
	}

	return magicmime.TypeByBuffer(blob[:])
}
