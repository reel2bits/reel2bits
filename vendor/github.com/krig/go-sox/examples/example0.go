// A simple example of using SoX libraries
package main

// Use this URL to import the go-sox library
import "github.com/krig/go-sox"
import "log"
import "flag"

// Reads an input file, applies volume and flanger effects,
// plays to output device.
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

	// The first effect in the effect chain must be something that can
	// source samples; in this case, we use the built-in handler that
	// inputs data from an audio file.
	e := sox.CreateEffect(sox.FindEffect("input"))
	e.Options(in)
	// This becomes the first "effect" in the chain
	chain.Add(e, in.Signal(), in.Signal())
	e.Release()

	// Create the `vol' effect, and initialise it with the desired parameters:
	e = sox.CreateEffect(sox.FindEffect("vol"))
	e.Options("3dB")
        // Add the effect to the end of the effects processing chain:
	chain.Add(e, in.Signal(), in.Signal())
	e.Release()

	// Create the `flanger' effect, and initialise it with default parameters:
	e = sox.CreateEffect(sox.FindEffect("flanger"))
	e.Options()
	chain.Add(e, in.Signal(), in.Signal())
	e.Release()

	// The last effect in the effect chain must be something that only consumes
	// samples; in this case, we use the built-in handler that outputs data.
	e = sox.CreateEffect(sox.FindEffect("output"))
	e.Options(out)
	chain.Add(e, in.Signal(), in.Signal())
	e.Release()

	// Flow samples through the effects processing chain until EOF is reached.
	chain.Flow()
}