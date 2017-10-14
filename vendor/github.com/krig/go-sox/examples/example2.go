// A simple example of using SoX libraries
package main

import (
	"log"
	"flag"
	"strconv"
	"fmt"
	"math"

	// Use this URL to import the go-sox library
	"github.com/krig/go-sox"
)

const (
	BLOCK_PERIOD = 0.025
	LINE = "==================================="
)

// Reads input file and displays a few seconds of wave-form, starting from
// a given time through the audio.   E.g. example2 song2.au 30.75 1
func main() {
	flag.Parse()

	// All libSoX applications must start by initializing the SoX library
	if !sox.Init() {
		log.Fatal("Failed to initialize SoX")
	}
	// Make sure to call Quit before terminating
	defer sox.Quit()

	if flag.NArg() < 1 {
		log.Fatal("Expected argument")
	}

	// Open the input file (with default parameters)
	in := sox.OpenRead(flag.Arg(0))
	if in == nil {
		log.Fatal("Failed to open input file")
	}
	// Close the file before exiting
	defer in.Release()

	// This example program requires that the audio has precisely 2 channels:
	if in.Signal().Channels() != 2 {
		log.Fatal("Input must be 2 channels")
	}

	start_secs := 0.0
	period := 2.0
	var err error

	// If given, read the start time:
	if flag.NArg() > 1 {
		start_secs, err = strconv.ParseFloat(flag.Arg(1), 64)
		if err != nil {
			log.Fatal(err)
		}
	}

	// If given, read the period of time to display:
	if flag.NArg() > 2 {
		period, err = strconv.ParseFloat(flag.Arg(2), 64)
		if err != nil {
			log.Fatal(err)
		}
	}

	// Calculate the start position in number of samples:
	seek := uint64(start_secs * float64(in.Signal().Rate()) * float64(in.Signal().Channels()) + 0.5)
	// Make sure that this is at a `wide sample' boundary:
	seek -= seek % uint64(in.Signal().Channels())
	// Move the file pointer to the desired starting position
	in.Seek(seek)

	// Convert block size (in seconds) to a number of samples:
	block_size := int64(BLOCK_PERIOD * float64(in.Signal().Rate()) * float64(in.Signal().Channels()) + 0.5)
	// Make sure that this is at a `wide sample' boundary:
	block_size -= block_size % int64(in.Signal().Channels())
	// Allocate a block of memory to store the block of audio samples:
	buf := make([]sox.Sample, block_size)

	// Read and process blocks of audio for the selected period or until EOF:
	for blocks := 0; in.Read(buf, uint(block_size)) == block_size && float64(blocks) * BLOCK_PERIOD < period; blocks++ {
		left := 0.0
		right := 0.0
		for i := int64(0); i < block_size; i++ {
			// convert the sample from SoX's internal format to a `float64' for
			// processing in this application:
			sample := sox.SampleToFloat64(buf[i])

			// The samples for each channel are interleaved; in this example
			// we allow only stereo audio, so the left channel audio can be found in
			// even-numbered samples, and the right channel audio in odd-numbered
			// samples:
			if (i & 1) != 0 {
				right = math.Max(right, math.Abs(sample))
			} else {
				left = math.Max(left, math.Abs(sample))
			}
		}
		// Build up the wave form by displaying the left & right channel
		// volume as a line length:
		l := int((1.0 - left) * 35.0 + 0.5)
		r := int((1.0 - right) * 35.0 + 0.5)
		fmt.Printf("%8.3f%36s|%s\n",
			start_secs + float64(blocks) * BLOCK_PERIOD,
			LINE[l:],
			LINE[r:])
	}
}
