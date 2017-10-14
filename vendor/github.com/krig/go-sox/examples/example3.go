// A simple example of using SoX libraries
package main

// Use this URL to import the go-sox library
import "github.com/krig/go-sox"
import "log"
import "flag"

// On an alsa capable system, plays an audio file starting 10 seconds in.
// Copes with sample-rate and channel change if necessary since its
// common for audio drivers to support a subset of rates and channel
// counts.
// E.g. example3 song2.ogg
//
// Can easily be changed to work with other audio device drivers supported
// by libSoX; e.g. "oss", "ao", "coreaudio", etc.
// See the soxformat(7) manual page.
func main() {
	flag.Parse()

	// All libSoX applications must start by initializing the SoX library
	if !sox.Init() {
		log.Fatal("Failed to initialize SoX")
	}
	// Make sure to call Quit before terminating
	defer sox.Quit()

	// Open the input file (with default parameters)
	in := sox.OpenRead(flag.Arg(0))
	if in == nil {
		log.Fatal("Failed to open input file")
	}
	// Close the file before exiting
	defer in.Release()

	// Open the output device: Specify the output signal characteristics.
	// Since we are using only simple effects, they are the same as the
	// input file characteristics.
	// Using "alsa" or "pulseaudio" should work for most files on Linux.
	// On other systems, other devices have to be used.
	out := sox.OpenWrite("default", in.Signal(), nil, "alsa")
	if out == nil {
		out = sox.OpenWrite("default", in.Signal(), nil, "pulseaudio")
		if out == nil {
			log.Fatal("Failed to open output device")
		}
	}
	// Close the output device before exiting
	defer out.Release()

	// Create an effects chain: Some effects need to know about the
	// input or output encoding so we provide that information here.
	chain := sox.CreateEffectsChain(in.Encoding(), out.Encoding())
	// Make sure to clean up!
	defer chain.Release()

	interm_signal := in.Signal().Copy()

	e := sox.CreateEffect(sox.FindEffect("input"))
	e.Options(in)
	chain.Add(e, interm_signal, in.Signal())
	e.Release()

	e = sox.CreateEffect(sox.FindEffect("trim"))
	e.Options("10")
	chain.Add(e, interm_signal, in.Signal())
	e.Release()

	if (in.Signal().Rate() != out.Signal().Rate()) {
		e = sox.CreateEffect(sox.FindEffect("rate"))
		e.Options()
		chain.Add(e, interm_signal, out.Signal())
		e.Release()
	}

	if (in.Signal().Channels() != out.Signal().Channels()) {
		e = sox.CreateEffect(sox.FindEffect("channels"))
		e.Options()
		chain.Add(e, interm_signal, out.Signal())
		e.Release()
	}

	// The last effect in the effect chain must be something that only consumes
	// samples; in this case, we use the built-in handler that outputs data.
	e = sox.CreateEffect(sox.FindEffect("output"))
	e.Options(out)
	chain.Add(e, interm_signal, in.Signal())
	e.Release()

	// Flow samples through the effects processing chain until EOF is reached.
	chain.Flow()
}
