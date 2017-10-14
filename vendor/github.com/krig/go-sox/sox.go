// Package sox is a set of bindings for the libSoX
// sound library. LibSoX is a library of sound sample
// file format readers/writers and sound effects
// processors. It is mainly developed for use by SoX
// but is useful for any sound application.
package sox

import (
	"unsafe"
	"math"
)

/*
#cgo pkg-config: sox
#include <sox.h>
#include <stdlib.h>
extern int go_flow_shim_impl(void* fn, sox_bool all_done);
sox_effect_handler_t const * go_sox_effect_fn_shim(sox_effect_fn_t const* fn);
int go_sox_flow_shim(sox_bool all_done, void *client_data);
sox_flow_effects_callback go_sox_get_flow_shim();
*/
import "C"

//export go_flow_shim_impl
func go_flow_shim_impl(fn unsafe.Pointer, all_done C.sox_bool) C.int {
	cfn := *(*func(bool) int)(fn)
	return C.int(cfn(all_done != 0))
}

const (
	// no, yes, or default (default usually implies some kind of auto-detect logic).
	NO = C.sox_option_no
	YES = C.sox_option_yes
	DEFAULT = C.sox_option_default

	// The libSoX-specific error codes.
	SUCCESS = C.SOX_SUCCESS // Function succeeded
	EOF = C.SOX_EOF		// End Of File or other error
	EHDR = C.SOX_EHDR	// Invalid Audio Header
	EFMT = C.SOX_EFMT	// Unsupported data format
	ENOMEM = C.SOX_ENOMEM	// Can't alloc memory
	EPERM = C.SOX_EPERM	// Operation not permitted
	ENOTSUP = C.SOX_ENOTSUP // Operation not supported
	EINVAL = C.SOX_EINVAL	// Invalid argument

	// Flags indicating whether optional features are present in this build of libSoX.
	HAVE_POPEN = C.sox_version_have_popen
	HAVE_MAGIC = C.sox_version_have_magic
	HAVE_THREADS = C.sox_version_have_threads
	HAVE_MEMOPEN = C.sox_version_have_memopen

	// Format of sample data.
	ENCODING_UNKNOWN = C.SOX_ENCODING_UNKNOWN	// encoding has not yet been determined
	ENCODING_SIGN2 = C.SOX_ENCODING_SIGN2		// signed linear 2's comp: Mac
	ENCODING_UNSIGNED = C.SOX_ENCODING_UNSIGNED	// unsigned linear: Sound Blaster
	ENCODING_FLOAT = C.SOX_ENCODING_FLOAT		// floating point (binary format)
	ENCODING_FLOAT_TEXT = C.SOX_ENCODING_FLOAT_TEXT // floating point (text format)
	ENCODING_FLAC = C.SOX_ENCODING_FLAC		// FLAC compression
	ENCODING_HCOM = C.SOX_ENCODING_HCOM		// Mac FSSD files with Huffman compression
	ENCODING_WAVPACK = C.SOX_ENCODING_WAVPACK	// WavPack with integer samples
	ENCODING_WAVPACKF = C.SOX_ENCODING_WAVPACKF	// WavPack with float samples
	ENCODING_ULAW = C.SOX_ENCODING_ULAW		// u-law signed logs: US telephony SPARC
	ENCODING_ALAW = C.SOX_ENCODING_ALAW		// A-law signed logs: non-US telephony Psion
	ENCODING_G721 = C.SOX_ENCODING_G721		// G.721 4-bit ADPCM
	ENCODING_G723 = C.SOX_ENCODING_G723		// G.723 3 or 5 bit ADPCM
	ENCODING_CL_ADPCM = C.SOX_ENCODING_CL_ADPCM	// Creative Labs 8 --> 234 bit Compressed PCM
	ENCODING_CL_ADPCM16 = C.SOX_ENCODING_CL_ADPCM16 // Creative Labs 16 --> 4 bit Compressed PCM
	ENCODING_MS_ADPCM = C.SOX_ENCODING_MS_ADPCM	// Microsoft Compressed PCM
	ENCODING_IMA_ADPCM = C.SOX_ENCODING_IMA_ADPCM	// IMA Compressed PCM
	ENCODING_OKI_ADPCM = C.SOX_ENCODING_OKI_ADPCM	// Dialogic/OKI Compressed PCM
	ENCODING_DPCM = C.SOX_ENCODING_DPCM		// Differential PCM: Fasttracker 2 (xi)
	ENCODING_DWVW = C.SOX_ENCODING_DWVW		// Delta Width Variable Word
	ENCODING_DWVWN = C.SOX_ENCODING_DWVWN		// Delta Width Variable Word N-bit
	ENCODING_GSM = C.SOX_ENCODING_GSM		// GSM 6.10 33byte frame lossy compression
	ENCODING_MP3 = C.SOX_ENCODING_MP3		// MP3 compression
	ENCODING_VORBIS = C.SOX_ENCODING_VORBIS		// Vorbis compression
	ENCODING_AMR_WB = C.SOX_ENCODING_AMR_WB		// AMR-WB compression
	ENCODING_AMR_NB = C.SOX_ENCODING_AMR_NB		// AMR-NB compression
	ENCODING_CVSD = C.SOX_ENCODING_CVSD		// Continuously Variable Slope Delta modulation
	ENCODING_LPC10 = C.SOX_ENCODING_LPC10		// Linear Predictive Coding

	// Flags for EncodingsInfo: lossless/lossy1/lossy2
	LOSSLESS = C.sox_encodings_none // No flags specified (implies lossless encoding).
	LOSSY1 = C.sox_encodings_lossy1 // Encode, decode: lossy once.
	LOSSY2 = C.sox_encodings_lossy2 // Encode, decode, encode, decode: lossy twice.

	// Type of plot.
	PLOT_OFF = C.sox_plot_off // No plot.
	PLOT_OCTAVE = C.sox_plot_octave // Octave plot.
	PLOT_GNUPLOT = C.sox_plot_gnuplot // Gnuplot plot.
	PLOT_DATA = C.sox_plot_data // Plot data.

	// Loop modes.
	LOOP_NONE = C.sox_loop_none // single-shot
	LOOP_FORWARD = C.sox_loop_forward // forward loop
	LOOP_FORWARD_BACK = C.sox_loop_forward_back // forward/back loop
	LOOP_8 = C.sox_loop_8 // 8 loops (??)
	LOOP_SUSTAIN_DECAY = C.sox_loop_sustain_decay // AIFF style, one sustain & one decay loop

	DEFAULT_CHANNELS = C.SOX_DEFAULT_CHANNELS
	DEFAULT_RATE = C.SOX_DEFAULT_RATE
	DEFAULT_PRECISION = C.SOX_DEFAULT_PRECISION
	DEFAULT_ENCODING = C.SOX_DEFAULT_ENCODING

	// Maximum number of loops supported by sox_oob_t
	MAX_NLOOPS = C.SOX_MAX_NLOOPS

	FILE_NOSTDIO = C.SOX_FILE_NOSTDIO
	FILE_DEVICE = C.SOX_FILE_DEVICE
	FILE_PHONY = C.SOX_FILE_PHONY
	FILE_REWIND = C.SOX_FILE_REWIND

)

// Version returns the version number
// string of libSoX, for example, "14.4.0".
func Version() string {
	return C.GoString(C.sox_version())
}

// FormatInit finds and loads format handler plugins.
// Returns true if successful.
func FormatInit() bool {
	ret := C.sox_format_init()
	return ret == C.SOX_SUCCESS
}

// FormatQuit unloads the format handler plugins.
func FormatQuit() {
	C.sox_format_quit()
}

// Init initializes the libsox effects library.
func Init() bool {
	ret := C.sox_init()
	return ret == C.SOX_SUCCESS
}

// Quit closes the effects library and unloads
// the format handler plugins.
func Quit() bool {
	ret := C.sox_quit()
	return ret == C.SOX_SUCCESS
}

func StrError(errno int) string {
	return C.GoString(C.sox_strerror(C.int(errno)))
}

// Format holds data passed to/from the format handler
type Format struct {
	cFormat *C.sox_format_t
}

// Sample is the native SoX audio sample type (int32)
type Sample int32

// SignalInfo holds signal parameters; members
// should be set to SOX_UNSPEC (= 0) if unknown.
type SignalInfo struct {
	cSignal *C.sox_signalinfo_t
}

// EncodingInfo holds encoding parameters.
type EncodingInfo struct {
	cEncoding *C.sox_encodinginfo_t
}

// EncodingsInfo holds basic information about an encoding.
type EncodingsInfo struct {
	Flags int // lossy once, lossy twice or lossless
	Name, Desc string
}

// FormatHandler structure defined by each format.
type FormatHandler struct {
	cHandler *C.sox_format_handler_t
}

// EffectsGlobals holds global parameters for effects.
type EffectsGlobals struct {
	cGlobals *C.sox_effects_globals_t
}

// EffectsChain holds a chain of effects to be applied to a stream.
type EffectsChain struct {
	cChain *C.sox_effects_chain_t

	// Used by FlowCallback to retain memory
	cbTmp func(all_done bool) int
}

// EffectHandler holds effect handler information.
type EffectHandler struct {
	cHandler *C.sox_effect_handler_t
}

// Effect holds effect information.
type Effect struct {
	cEffect *C.sox_effect_t
}

// Memstream is a holder for memory
// buffer information filled in by
// OpenMemstreamWrite. It can be passed
// directly to OpenMemRead().
type Memstream struct {
	buffer *C.char
	length C.size_t
}

// Comments holds file's metadata, access via sox_*_comments functions.
type Comments struct {
	cComments *C.sox_comments_t
}

// Release closes an encoding or decoding session.
func (f *Format) Release() {
	C.sox_close(f.cFormat)
	f.cFormat = nil
}

// Filename.
func (f *Format) Filename() string {
	return C.GoString(f.cFormat.filename)
}

// Signal specifications for reader (decoder) or writer (encoder):
// sample rate, number of channels, precision, length, headroom multiplier.
// Any info specified by the user is here on entry to startread or
// startwrite. Info will be SOX_UNSPEC if the user provided no info.
// At exit from startread, should be completely filled in, using
// either data from the file's headers (if available) or whatever
// the format is guessing/assuming (if header data is not available).
// At exit from startwrite, should be completely filled in, using
// either the data that was specified, or values chosen by the format
// based on the format's defaults or capabilities.
func (f *Format) Signal() *SignalInfo {
	var s SignalInfo
	s.cSignal = &f.cFormat.signal
	return &s
}

// Encoding specifications for reader (decoder) or writer (encoder):
//  encoding (sample format), bits per sample, compression rate, endianness.
//  Should be filled in by startread. Values specified should be used
//  by startwrite when it is configuring the encoding parameters.
func (f *Format) Encoding() *EncodingInfo {
	var e EncodingInfo
	e.cEncoding = &f.cFormat.encoding
	return &e
}

// Type of file, as determined by header inspection or libmagic.
func (f *Format) Type() string {
	return C.GoString(f.cFormat.filetype)
}

// Seekable returns true if seek can be used on this file.
func (f *Format) Seekable() bool {
	return f.cFormat.seekable != 0
}

// Read reads samples from a decoding session into a sample buffer.
func (f *Format) Read(buffer []Sample, num uint) int64 {
	return int64(C.sox_read(f.cFormat, (*C.sox_sample_t)(unsafe.Pointer(&buffer[0])), C.size_t(num)))
}

// Write writes samples to an encoding session from a sample buffer.
func (f *Format) Write(buffer []Sample, num uint) int64 {
	return int64(C.sox_write(f.cFormat, (*C.sox_sample_t)(unsafe.Pointer(&buffer[0])), C.size_t(num)))
}

// Seek sets the location at which next samples will be decoded. Returns true if successful.
func (f *Format) Seek(offset uint64) bool {
	return C.sox_seek(f.cFormat, C.sox_uint64_t(offset), C.SOX_SEEK_SET) == C.SOX_SUCCESS
}

// Comments returns out-of-band metadata
func (f *Format) Comments() *Comments {
	var c Comments
	c.cComments = &f.cFormat.oob.comments
	return &c
}

// DeleteComments deletes all out-of-band metadata
func (f *Format) DeleteComments() {
	C.sox_delete_comments(&f.cFormat.oob.comments)
}

func NewEncodingInfo(encoding C.sox_encoding_t, bitsPerSample uint, compression float64, oppositeEndian bool) *EncodingInfo {
	var e EncodingInfo
	e.cEncoding = &C.sox_encodinginfo_t{}
	e.cEncoding.encoding = encoding
	e.cEncoding.bits_per_sample = C.unsigned(bitsPerSample)
	e.cEncoding.compression = C.double(compression)
	e.cEncoding.reverse_bytes = NO
	e.cEncoding.reverse_nibbles = NO
	if oppositeEndian {
		e.cEncoding.opposite_endian = C.sox_bool(1)
	} else {
		e.cEncoding.opposite_endian = C.sox_bool(0)
	}
	return &e
}

func NewSignalInfo(rate float64, channels, precision uint, length uint64, mult *float64) *SignalInfo {
	var s SignalInfo
	s.cSignal = &C.sox_signalinfo_t{}
	s.cSignal.rate = C.sox_rate_t(rate)
	s.cSignal.channels = C.unsigned(channels)
	s.cSignal.precision = C.unsigned(precision)
	s.cSignal.length = C.sox_uint64_t(length)
	if mult != nil {
		var d C.double
		d = C.double(*mult)
		s.cSignal.mult = &d
	}
	return &s
}

// Rate = samples per second, 0 if unknown
func (s *SignalInfo) Rate() float64 {
	return float64(s.cSignal.rate)
}

// Channels = number of sound channels, 0 if unknown
func (s *SignalInfo) Channels() uint {
	return uint(s.cSignal.channels)
}

// Precision = bits per sample, 0 if unknown
func (s *SignalInfo) Precision() uint {
	return uint(s.cSignal.precision)
}

// Length = samples * chans in file, 0 if unknown, -1 if unspecified
func (s *SignalInfo) Length() uint64 {
	return uint64(s.cSignal.length)
}

// Mult = Effects headroom multiplier; (value, set/not set)
func (s *SignalInfo) Mult() (float64, bool) {
	if s.cSignal.mult != nil {
		return float64(*s.cSignal.mult), true
	}
	return 0.0, false
}

// Returns a copy of the signalinfo
func (s *SignalInfo) Copy() *SignalInfo {
	ret := &SignalInfo{}
	ret.cSignal = &C.sox_signalinfo_t{}
	ret.cSignal.rate = s.cSignal.rate
	ret.cSignal.channels = s.cSignal.channels
	ret.cSignal.precision = s.cSignal.precision
	ret.cSignal.length = s.cSignal.length
	ret.cSignal.mult = s.cSignal.mult
	return ret
}

// OpenRead opens a decoding session for a file. Returned handle
// must be closed with (*Format).Release().
// Returns the handle for the new session, or nil on failure.
func OpenRead(path string) *Format {
	cpath := C.CString(path)
	var fmt Format
	fmt.cFormat = C.sox_open_read(cpath, nil, nil, nil)
	C.free(unsafe.Pointer(cpath))
	if fmt.cFormat == nil {
		return nil
	}
	return &fmt
}

// OpenMemRead opens a decoding session for a memory buffer.
// Returned handle must be closed with (*Format).Release().
// Returns the handle for the new session, or nil
// on failure.
func OpenMemRead(buffer interface{}) *Format {
	var fmt Format
	switch buffer := buffer.(type) {
	case []byte:
		fmt.cFormat = C.sox_open_mem_read(unsafe.Pointer(&buffer[0]), C.size_t(len(buffer)), nil, nil, nil)
	case *Memstream:
		fmt.cFormat = C.sox_open_mem_read(unsafe.Pointer(buffer.buffer), buffer.length, nil, nil, nil)
	}
	if fmt.cFormat == nil {
		return nil
	}
	return &fmt
}

// FormatSupportsEncoding returns true if the format handler for
// the specified file type supports the specified encoding.
func FormatSupportsEncoding(path string, encoding *EncodingInfo) bool {
	cpath := C.CString(path)
	defer C.free(unsafe.Pointer(cpath))
	return int(C.sox_format_supports_encoding(cpath, nil, encoding.cEncoding)) != 0
}

// FormatSupportsEncoding2 returns true if the format handler for
// the specified file type supports the specified encoding.
func FormatSupportsEncoding2(path, filetype string, encoding *EncodingInfo) bool {
	cpath := C.CString(path)
	defer C.free(unsafe.Pointer(cpath))
	ctype := C.CString(filetype)
	defer C.free(unsafe.Pointer(ctype))
	return int(C.sox_format_supports_encoding(cpath, ctype, encoding.cEncoding)) != 0
}

// maybeCSignal returns nil if the owned signal is NULL.
func maybeCSignal(signal *SignalInfo) *C.sox_signalinfo_t {
	if signal != nil {
		return signal.cSignal
	}
	return nil
}

// maybeCSEncoding returns nil if the owned encoding is NULL.
func maybeCEncoding(encoding *EncodingInfo) *C.sox_encodinginfo_t {
	if encoding != nil {
		return encoding.cEncoding
	}
	return nil
}

// maybeCString returns a C string for a given string, or nil
// for anything else.
func maybeCString(s interface{}) *C.char {
	switch s := s.(type) {
	case string:
		return C.CString(s)
	}
	return nil
}

// OpenWrite opens an encoding session for a file.
// Returned handle must be closed with .Release().
func OpenWrite(path string, signal *SignalInfo, encoding *EncodingInfo, filetype interface{}) *Format {
	var fmt Format
	cpath := C.CString(path)
	cfiletype := maybeCString(filetype)
	fmt.cFormat = C.sox_open_write(cpath,
		maybeCSignal(signal),
		maybeCEncoding(encoding),
		cfiletype,
		nil,
		nil)
	C.free(unsafe.Pointer(cpath))
	if cfiletype != nil {
		C.free(unsafe.Pointer(cfiletype))
	}
	if fmt.cFormat == nil {
		return nil
	}
	return &fmt
}

// OpenMemWrite opens an encoding session for a memory buffer.
// Returned handle must be closed with .Release().
func OpenMemWrite(buffer []byte, signal *SignalInfo, encoding *EncodingInfo, filetype interface{}) *Format {
	var fmt Format
	cfiletype := maybeCString(filetype)
	fmt.cFormat = C.sox_open_mem_write(unsafe.Pointer(&buffer[0]),
		C.size_t(len(buffer)),
		maybeCSignal(signal),
		maybeCEncoding(encoding),
		cfiletype,
		nil)
	if cfiletype != nil {
		C.free(unsafe.Pointer(cfiletype))
	}
	if fmt.cFormat == nil {
		return nil
	}
	return &fmt
}

// NewMemstream creates a new memory buffer holder.
func NewMemstream() *Memstream {
	var ms Memstream
	return &ms
}

// Bytes returns a copy of the written memory buffer
// as a Go byte array.
func (m *Memstream) Bytes() []byte {
	return C.GoBytes(unsafe.Pointer(m.buffer), C.int(m.length))
}

// Release the memstream and free the allocated memory
func (m *Memstream) Release() {
	if m.buffer != nil {
		C.free(unsafe.Pointer(m.buffer))
		m.buffer = nil
	}
}

// OpenMemstreamWrite opens an encoding session for a memstream buffer.
// Returned handle must be closed with .Release()
func OpenMemstreamWrite(memstream *Memstream, signal *SignalInfo, encoding *EncodingInfo, filetype interface{}) *Format {
	var fmt Format
	cfiletype := maybeCString(filetype)
	fmt.cFormat = C.sox_open_memstream_write(&memstream.buffer, &memstream.length,
		maybeCSignal(signal),
		maybeCEncoding(encoding),
		cfiletype,
		nil)
	if cfiletype != nil {
		C.free(unsafe.Pointer(cfiletype))
	}
	if fmt.cFormat == nil {
		return nil
	}
	return &fmt
}

// FindFormat finds a format handler by name.
func FindFormat(name string, ignore_devices bool) *FormatHandler {
	var fmt FormatHandler
	cname := C.CString(name)
	fmt.cHandler = C.sox_find_format(cname, C.sox_bool(bool2int(ignore_devices)))
	C.free(unsafe.Pointer(cname))
	return &fmt
}

// GetEffectsGlobals returns global parameters for effects.
func GetEffectsGlobals() *EffectsGlobals {
	var g EffectsGlobals
	g.cGlobals = C.sox_get_effects_globals()
	return &g
}

// CreateEffectsChain initializes an effects chain.
// Returned handle must be closed with .Release().
func CreateEffectsChain(in *EncodingInfo, out *EncodingInfo) *EffectsChain {
	var chain EffectsChain
	chain.cChain = C.sox_create_effects_chain(in.cEncoding, out.cEncoding)
	return &chain
}

// Release the memory used by the effects chain.
func (c *EffectsChain) Release() {
	C.sox_delete_effects_chain(c.cChain)
}

// Add the given effect to the effects chain.
// Returns true if successful.
func (c *EffectsChain) Add(effect *Effect, in, out *SignalInfo) bool {
	return C.sox_add_effect(c.cChain, effect.cEffect, in.cSignal, out.cSignal) == C.SOX_SUCCESS
}

// PushLast adds an already-initialized effect to the end of the chain.
func (c *EffectsChain) PushLast(effect* Effect) {
	C.sox_push_effect_last(c.cChain, effect.cEffect)
}

// PopLast removes and returns an effect from the end of the chain.
func (c *EffectsChain) PopLast() *Effect {
	var e Effect
	e.cEffect = C.sox_pop_effect_last(c.cChain)
	if e.cEffect == nil {
		return nil
	}
	return &e
}

// DeleteLast shuts down and deletes the last effect in the chain.
func (c *EffectsChain) DeleteLast() {
	C.sox_delete_effect_last(c.cChain)
}

// DeleteAll shuts down and deletes all effects in the chain.
func (c *EffectsChain) DeleteAll() {
	C.sox_delete_effects(c.cChain)
}

// Flow runs the effects chain, returns true if successful.
func (c *EffectsChain) Flow() bool {
	return C.sox_flow_effects(c.cChain, nil, nil) == C.SOX_SUCCESS
}

func (c *EffectsChain) FlowCallback(fn func(all_done bool) int) bool {
	c.cbTmp = fn
	return C.sox_flow_effects(c.cChain, C.go_sox_get_flow_shim(), unsafe.Pointer(&c.cbTmp)) == C.SOX_SUCCESS
}

// Clips returns the number of clips that occurred while running an effects chain.
func (c *EffectsChain) Clips() uint64 {
	return uint64(C.sox_effects_clips(c.cChain))
}

// Name returns the effect name
func (h *EffectHandler) Name() string {
	return C.GoString(h.cHandler.name)
}

// Usage returns a short explanation of the parameters accepted by the effect
func (h *EffectHandler) Usage() string {
	return C.GoString(h.cHandler.usage)
}

// Flags returns the combination of effect flags
func (h *EffectHandler) Flags() uint {
	return uint(h.cHandler.flags)
}


// FindEffect finds the effect handler with the given name.
func FindEffect(name string) *EffectHandler {
	var h EffectHandler
	cname := C.CString(name)
	h.cHandler = C.sox_find_effect(cname)
	C.free(unsafe.Pointer(cname))
	return &h
}

// CreateEffect creates an effect using the given handler.
func CreateEffect(handler *EffectHandler) *Effect {
	var e Effect
	e.cEffect = C.sox_create_effect(handler.cHandler)
	return &e
}

// Stop an effect (calls stop on each of its flows).
func (e *Effect) Stop() {
	C.sox_stop_effect(e.cEffect)
}

// Release the memory held by the effect.
func (e *Effect) Release() {
	C.free(unsafe.Pointer(e.cEffect))
	e.cEffect = nil
}

// Options applies the given command-line options to the effect.
func (e *Effect) Options(args ...interface{}) int {
	if len(args) == 0 {
		return int(C.sox_effect_options(e.cEffect, 0, nil))
	}
	if len(args) > 10 {
		panic("Too many arguments to sox.Effect.Options()")
	}
	var cargs [10](*C.char)
	n := len(args)
	for i, v := range args {
		switch v := v.(type) {
		case *Format:
			cargs[i] = (*C.char)(unsafe.Pointer(v.cFormat))
		case string:
			cargs[i] = C.CString(v)
		}
	}

	return int(C.sox_effect_options(e.cEffect, C.int(n), (&cargs[0])))
}

// GetEncodingsInfo returns an array of available encodings.
func GetEncodingsInfo() (info []EncodingsInfo) {
	cinfo := C.sox_get_encodings_info()
	if cinfo == nil {
		return
	}
	var pt C.sox_encodings_info_t
	var p *C.sox_encodings_info_t
	q := uintptr(unsafe.Pointer(cinfo))
	for {
		p = (*C.sox_encodings_info_t)(unsafe.Pointer(q))
		if p.name == nil {
			break
		}
		var e EncodingsInfo
		e.Flags = int(p.flags)
		e.Name = C.GoString(p.name)
		e.Desc = C.GoString(p.desc)
		info = append(info, e)
		q += unsafe.Sizeof(pt)
	}
	return
}

// GetEffectHandlers returns an array containing the known effect handlers.
func GetEffectHandlers() (handlers []EffectHandler) {
	effect_fns := C.sox_get_effect_fns()
	if effect_fns == nil {
		return
	}
	q := uintptr(unsafe.Pointer(effect_fns))
	for {
		effect_fns = (*C.sox_effect_fn_t)(unsafe.Pointer(q))
		if *effect_fns == nil {
			break
		}
		var handler EffectHandler
		handler.cHandler = C.go_sox_effect_fn_shim(effect_fns)
		handlers = append(handlers, handler)
		q += unsafe.Sizeof(q)
	}
	return
}

// Precision: Given an encoding (for example, SIGN2) and the encoded bits_per_sample (for
// example, 16), returns the number of useful bits per sample in the decoded data
// (for example, 16), or returns 0 to indicate that the value returned by the
// format handler should be used instead of a pre-determined precision.
// @returns the number of useful bits per sample in the decoded data (for example
// 16), or returns 0 to indicate that the value returned by the format handler
// should be used instead of a pre-determined precision.
func Precision(encoding int, bits_per_sample uint) uint {
	return uint(C.sox_precision(C.sox_encoding_t(encoding), C.unsigned(bits_per_sample)))
}

// Num returns the number of items in the metadata block.
func (c *Comments) Num() int {
	return int(C.sox_num_comments(*c.cComments))
}

// Append adds an "id=value" item to the metadata block.
func (c *Comments) Append(item string) {
	citem := C.CString(item)
	defer C.free(unsafe.Pointer(citem))
	C.sox_append_comment(c.cComments, citem)
}

// AppendN adds a newline-delimited list of "id=value" items to the metadata block.
func (c *Comments) AppendN(item string) {
	citem := C.CString(item)
	defer C.free(unsafe.Pointer(citem))
	C.sox_append_comments(c.cComments, citem)
}

// Find returns value if "id=value" is found, else nil
func (c *Comments) Find(id string) interface{} {
	cid := C.CString(id)
	defer C.free(unsafe.Pointer(cid))
	ret := C.sox_find_comment(*c.cComments, cid)
	if ret == nil {
		return nil
	}
	return C.GoString(ret)
}

// SampleToUInt32 converts sox.Sample to an unsigned 32-bit integer
func SampleToUInt32(d Sample) uint32 {
	return uint32(((d) ^ math.MinInt32))
}

// SampleToInt32 converts sox.Sample to a signed 32-bit integer
func SampleToInt32(d Sample) int32 {
	return int32(d)
}

// SampleToFloat64 converts sox.Sample to a float64
func SampleToFloat64(d Sample) float64 {
	return ((float64(d)) * (1.0 / (float64(math.MaxInt32) + 1.0)))
}

// bool2int converts a bool to 1 for true and 0 for false.
func bool2int(b bool) int {
	if b {
		return 1
	}
	return 0
}
