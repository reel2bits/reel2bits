package sanitize

/*
 * Based on https://github.com/kennygrant/sanitize/blob/master/sanitize.go
 * See https://github.com/kennygrant/sanitize/blob/master/LICENSE
 */

import (
	"bytes"
	"path"
	"regexp"
	"strings"
)

// A very limited list of transliterations to catch common european names translated to urls.
// This set could be expanded with at least caps and many more characters.
var transliterations = map[rune]string{
	'À': "A",
	'Á': "A",
	'Â': "A",
	'Ã': "A",
	'Ä': "A",
	'Å': "AA",
	'Æ': "AE",
	'Ç': "C",
	'È': "E",
	'É': "E",
	'Ê': "E",
	'Ë': "E",
	'Ì': "I",
	'Í': "I",
	'Î': "I",
	'Ï': "I",
	'Ð': "D",
	'Ł': "L",
	'Ñ': "N",
	'Ò': "O",
	'Ó': "O",
	'Ô': "O",
	'Õ': "O",
	'Ö': "O",
	'Ø': "OE",
	'Ù': "U",
	'Ú': "U",
	'Ü': "U",
	'Û': "U",
	'Ý': "Y",
	'Þ': "Th",
	'ß': "ss",
	'à': "a",
	'á': "a",
	'â': "a",
	'ã': "a",
	'ä': "a",
	'å': "aa",
	'æ': "ae",
	'ç': "c",
	'è': "e",
	'é': "e",
	'ê': "e",
	'ë': "e",
	'ì': "i",
	'í': "i",
	'î': "i",
	'ï': "i",
	'ð': "d",
	'ł': "l",
	'ñ': "n",
	'ń': "n",
	'ò': "o",
	'ó': "o",
	'ô': "o",
	'õ': "o",
	'ō': "o",
	'ö': "o",
	'ø': "oe",
	'ś': "s",
	'ù': "u",
	'ú': "u",
	'û': "u",
	'ū': "u",
	'ü': "u",
	'ý': "y",
	'þ': "th",
	'ÿ': "y",
	'ż': "z",
	'Œ': "OE",
	'œ': "oe",
}

// A list of characters we consider separators in normal strings and replace with our canonical separator _ rather than removing.
var (
	separators = regexp.MustCompile(`[ &_=+:]`)

	dashes = regexp.MustCompile(`[\-]+`)
)

// Accents replaces a set of accented characters with ascii equivalents.
func Accents(s string) string {
	// Replace some common accent characters
	b := bytes.NewBufferString("")
	for _, c := range s {
		// Check transliterations first
		if val, ok := transliterations[c]; ok {
			b.WriteString(val)
		} else {
			b.WriteRune(c)
		}
	}
	return b.String()
}

// cleanString replaces separators with - and removes characters listed in the regexp provided from string.
// Accents, spaces, and all characters not in A-Za-z0-9 are replaced.
func cleanString(s string, r *regexp.Regexp) string {

	// Remove any trailing space to avoid ending on -
	s = strings.Trim(s, " ")

	// Flatten accents first so that if we remove non-ascii we still get a legible name
	s = Accents(s)

	// Replace certain joining characters with an underscore
	s = separators.ReplaceAllString(s, "_")

	// Remove all other unrecognised characters - NB we do allow any printable characters
	s = r.ReplaceAllString(s, "")

	// Remove any multiple dashes caused by replacements above
	s = dashes.ReplaceAllString(s, "-")

	return s
}

// We are very restrictive as this could be intended for ascii url slugs
var illegalPath = regexp.MustCompile(`[^[:alnum:]\~\-\./]`)

// Filename sanitization
func Filename(s string) string {
	filePath := strings.Replace(s, "..", "", -1)
	filePath = path.Clean(filePath)

	// Remove illegal characters for paths, flattening accents and replacing some common separators with -
	filePath = cleanString(filePath, illegalPath)

	// NB this may be of length 0, caller must check
	return filePath
}
