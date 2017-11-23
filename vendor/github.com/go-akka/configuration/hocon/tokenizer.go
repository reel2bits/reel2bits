package hocon

import (
	"bytes"
	"fmt"
	"strings"
)

const (
	HoconNotInUnquotedKey  = "$\"{}[]:=+,#`^?!@*&\\."
	HoconNotInUnquotedText = "$\"{}[]:=+,#`^?!@*&\\"
)

type Tokenizer struct {
	text       string
	index      int
	indexStack *Stack
}

func NewTokenizer(text string) *Tokenizer {
	return &Tokenizer{
		indexStack: NewStack(),
		text:       text,
	}
}

func (p *Tokenizer) Push() {
	p.indexStack.Push(p.index)
}

func (p *Tokenizer) Pop() {
	index, err := p.indexStack.Pop()
	if err != nil {
		panic(err)
	}
	p.index = index
}

func (p *Tokenizer) EOF() bool {
	return p.index >= len(p.text)
}

func (p *Tokenizer) Matches(pattern string) bool {

	if len(pattern)+p.index > len(p.text) {
		return false
	}

	selected := string(p.text[p.index : p.index+len(pattern)])

	if selected == pattern {
		return true
	}

	return false
}

func (p *Tokenizer) MatchesMore(patterns []string) bool {
	for _, pattern := range patterns {
		if len(pattern)+p.index >= len(p.text) {
			continue
		}

		if string(p.text[p.index:p.index+len(pattern)]) == pattern {
			return true
		}
	}
	return false
}

func (p *Tokenizer) Take(length int) string {
	if p.index+length > len(p.text) {
		return ""
	}

	str := string(p.text[p.index : p.index+length])
	p.index += length
	return str
}

func (p *Tokenizer) Peek() byte {
	if p.EOF() {
		return 0
	}

	return p.text[p.index]
}

func (p *Tokenizer) TakeOne() byte {
	if p.EOF() {
		return 0
	}

	b := p.text[p.index]
	p.index += 1
	return b
}

func (p *Tokenizer) PullWhitespace() {
	for !p.EOF() && isWhitespace(p.Peek()) {
		p.TakeOne()
	}
}

type HoconTokenizer struct {
	*Tokenizer
}

func NewHoconTokenizer(text string) *HoconTokenizer {
	return &HoconTokenizer{NewTokenizer(text)}
}

func (p *HoconTokenizer) PullWhitespaceAndComments() {
	for {
		p.PullWhitespace()
		for p.IsStartOfComment() {
			p.PullComment()
		}

		if !p.IsWhitespace() {
			break
		}
	}
}

func (p *HoconTokenizer) PullRestOfLine() string {
	buf := bytes.NewBuffer(nil)

	for !p.EOF() {
		c := p.TakeOne()
		if c == '\n' {
			break
		}

		if c == '\r' {
			continue
		}
		if err := buf.WriteByte(c); err != nil {
			panic(err)
		}
	}

	return strings.TrimSpace(buf.String())
}

func (p *HoconTokenizer) PullNext() (token *Token) {

	p.PullWhitespaceAndComments()
	if p.IsDot() {
		token = p.PullDot()
	} else if p.IsObjectStart() {
		token = p.PullStartOfObject()
	} else if p.IsEndOfObject() {
		token = p.PullEndOfObject()
	} else if p.IsAssignment() {
		token = p.PullAssignment()
	} else if p.IsPlusAssignment() {
		token = p.PullPlusAssignment()
	} else if p.IsInclude() {
		token = p.PullInclude()
	} else if p.isStartOfQuotedKey() {
		token = p.PullQuotedKey()
	} else if p.IsUnquotedKeyStart() {
		token = p.PullUnquotedKey()
	} else if p.IsArrayStart() {
		token = p.PullArrayStart()
	} else if p.IsArrayEnd() {
		token = p.PullArrayEnd()
	} else if p.EOF() {
		token = NewToken(TokenTypeEoF)
	}

	if token != nil {
		return
	}

	panic(fmt.Errorf("unknown token, offset: %d", p.index))
}

func (p *HoconTokenizer) isStartOfQuotedKey() bool {
	return p.Matches("\"")
}

func (p *HoconTokenizer) PullArrayEnd() *Token {
	p.TakeOne()
	return NewToken(TokenTypeArrayEnd)
}

func (p *HoconTokenizer) IsArrayEnd() bool {
	return p.Matches("]")
}

func (p *HoconTokenizer) IsArrayStart() bool {
	return p.Matches("[")
}

func (p *HoconTokenizer) PullArrayStart() *Token {
	p.TakeOne()
	return NewToken(TokenTypeArrayStart)
}

func (p *HoconTokenizer) PullDot() *Token {
	p.TakeOne()
	return NewToken(TokenTypeDot)
}

func (p *HoconTokenizer) PullComma() *Token {
	p.TakeOne()
	return NewToken(TokenTypeComma)
}

func (p *HoconTokenizer) PullNewline() *Token {
	p.Take(2)
	return NewToken(TokenTypeNewline)
}

func (p *HoconTokenizer) PullStartOfObject() *Token {
	p.TakeOne()
	return NewToken(TokenTypeObjectStart)
}

func (p *HoconTokenizer) PullEndOfObject() *Token {
	p.TakeOne()
	return NewToken(TokenTypeObjectEnd)
}

func (p *HoconTokenizer) PullAssignment() *Token {
	p.TakeOne()
	return NewToken(TokenTypeAssign)
}

func (p *HoconTokenizer) PullPlusAssignment() *Token {
	p.Take(2)
	return NewToken(TokenTypePlusAssign)
}

func (p *HoconTokenizer) IsComma() bool {
	return p.Matches(",")
}

func (p *HoconTokenizer) IsNewline() bool {
	return p.Matches(`\n`)
}

func (p *HoconTokenizer) IsDot() bool {
	return p.Matches(".")
}

func (p *HoconTokenizer) IsObjectStart() bool {
	return p.Matches("{")
}

func (p *HoconTokenizer) IsEndOfObject() bool {
	return p.Matches("}")
}

func (p *HoconTokenizer) IsAssignment() bool {
	return p.MatchesMore([]string{"=", ":"})
}

func (p *HoconTokenizer) IsPlusAssignment() bool {
	return p.Matches("+=")
}

func (p *HoconTokenizer) IsStartOfQuotedText() bool {
	return p.Matches("\"")
}

func (p *HoconTokenizer) IsStartOfTripleQuotedText() bool {
	return p.Matches("\"\"\"")
}

func (p *HoconTokenizer) PullComment() *Token {
	p.PullRestOfLine()
	return NewToken(TokenTypeComment)
}

func (p *HoconTokenizer) PullUnquotedKey() *Token {
	buf := bytes.NewBuffer(nil)
	for !p.EOF() && p.IsUnquotedKey() {
		if err := buf.WriteByte(p.TakeOne()); err != nil {
			panic(err)
		}
	}

	return DefaultToken.Key(strings.TrimSpace(buf.String()))
}

func (p *HoconTokenizer) IsUnquotedKey() bool {
	return !p.EOF() && !p.IsStartOfComment() && (strings.IndexByte(HoconNotInUnquotedKey, p.Peek()) == -1)
}

func (p *HoconTokenizer) IsUnquotedKeyStart() bool {
	return !p.EOF() && !p.IsWhitespace() && !p.IsStartOfComment() && (strings.IndexByte(HoconNotInUnquotedKey, p.Peek()) == -1)
}

func (p *HoconTokenizer) IsWhitespace() bool {
	return isWhitespace(p.Peek())
}

func (p *HoconTokenizer) IsWhitespaceOrComment() bool {
	return p.IsWhitespace() || p.IsStartOfComment()
}

func (p *HoconTokenizer) PullTripleQuotedText() *Token {
	buf := bytes.NewBuffer(nil)
	p.Take(3)
	for !p.EOF() && !p.Matches("\"\"\"") {
		if err := buf.WriteByte(p.Peek()); err != nil {
			panic(err)
		}
		p.TakeOne()
	}
	p.Take(3)
	return DefaultToken.LiteralValue(buf.String())
}

func (p *HoconTokenizer) PullQuotedText() *Token {
	buf := bytes.NewBuffer(nil)
	p.TakeOne()
	for !p.EOF() && !p.Matches("\"") {
		if p.Matches("\\") {
			if _, err := buf.WriteString(p.pullEscapeSequence()); err != nil {
				panic(err)
			}
		} else {
			if err := buf.WriteByte(p.Peek()); err != nil {
				panic(err)
			}
			p.TakeOne()
		}
	}
	p.TakeOne()
	return DefaultToken.LiteralValue(buf.String())
}

func (p *HoconTokenizer) PullQuotedKey() *Token {
	buf := bytes.NewBuffer(nil)
	p.TakeOne()
	for !p.EOF() && !p.Matches("\"") {
		if p.Matches("\\") {
			if _, err := buf.WriteString(p.pullEscapeSequence()); err != nil {
				panic(err)
			}
		} else {
			if err := buf.WriteByte(p.Peek()); err != nil {
				panic(err)
			}
			p.TakeOne()
		}
	}
	p.TakeOne()
	return DefaultToken.Key(buf.String())
}

func (p *HoconTokenizer) PullInclude() *Token {
	p.Take(len("include"))
	p.PullWhitespaceAndComments()
	rest := p.PullQuotedText()
	unQuote := rest.value
	return DefaultToken.Include(unQuote)
}

func (p *HoconTokenizer) pullEscapeSequence() string {
	p.TakeOne()
	escaped := p.TakeOne()
	switch escaped {
	case '"':
		return ("\"")
	case '\\':
		return ("\\")
	case '/':
		return ("/")
	case 'b':
		return ("\b")
	case 'f':
		return ("\f")
	case 'n':
		return ("\n")
	case 'r':
		return ("\r")
	case 't':
		return ("\t")
	case 'u':
		utf8Code := "\\u" + strings.ToLower(p.Take(4))
		utf8Str := ""
		if _, err := fmt.Sscanf(utf8Code, "%s", &utf8Str); err != nil {
			panic(err)
		}
		return utf8Str
	default:
		panic(fmt.Errorf("Unknown escape code: %v", escaped))
	}
}

func (p *HoconTokenizer) IsStartOfComment() bool {
	return p.MatchesMore([]string{"#", "//"})
}

func (p *HoconTokenizer) PullValue() *Token {
	if p.IsObjectStart() {
		return p.PullStartOfObject()
	}

	if p.IsStartOfTripleQuotedText() {
		return p.PullTripleQuotedText()
	}

	if p.IsStartOfQuotedText() {
		return p.PullQuotedText()
	}

	if p.isUnquotedText() {
		return p.pullUnquotedText()
	}

	if p.IsArrayStart() {
		return p.PullArrayStart()
	}

	if p.IsArrayEnd() {
		return p.PullArrayEnd()
	}

	if p.IsSubstitutionStart() {
		return p.pullSubstitution()
	}

	panic(fmt.Errorf("Expected value: Null literal, Array, Quoted Text, Unquoted Text, Triple quoted Text, Object or End of array"))
}

func (p *HoconTokenizer) IsSubstitutionStart() bool {
	return p.MatchesMore([]string{"${", "${?"})
}

func (p *HoconTokenizer) IsInclude() bool {
	p.Push()
	defer func() {
		recover()
		p.Pop()
	}()
	if p.Matches("include") {
		p.Take(len("include"))
		if p.IsWhitespaceOrComment() {
			p.PullWhitespaceAndComments()
			if p.IsStartOfQuotedText() {
				p.PullQuotedText()
				return true
			}
		}
	}

	return false
}

func (p *HoconTokenizer) pullSubstitution() *Token {
	buf := bytes.NewBuffer(nil)
	p.Take(2)
	isOptional := false
	if p.Peek() == '?' {
		p.TakeOne()
		isOptional = true
	}

	for !p.EOF() && p.isUnquotedText() {
		if err := buf.WriteByte(p.TakeOne()); err != nil {
			panic(err)
		}
	}
	p.TakeOne()
	return DefaultToken.Substitution(buf.String(), isOptional)
}

func (p *HoconTokenizer) IsSpaceOrTab() bool {
	return p.MatchesMore([]string{" ", "\t"})
}

func (p *HoconTokenizer) IsStartSimpleValue() bool {
	if p.IsSpaceOrTab() {
		return true
	}

	if p.isUnquotedText() {
		return true
	}

	return false
}

func (p *HoconTokenizer) PullSpaceOrTab() *Token {
	buf := bytes.NewBuffer(nil)
	for p.IsSpaceOrTab() {
		if err := buf.WriteByte(p.TakeOne()); err != nil {
			panic(err)
		}
	}
	return DefaultToken.LiteralValue(buf.String())
}

func (p *HoconTokenizer) pullUnquotedText() *Token {
	buf := bytes.NewBuffer(nil)
	for !p.EOF() && p.isUnquotedText() {
		if err := buf.WriteByte(p.TakeOne()); err != nil {
			panic(err)
		}
	}
	return DefaultToken.LiteralValue(buf.String())
}

func (p *HoconTokenizer) isUnquotedText() bool {
	return !p.EOF() && !p.IsWhitespace() && !p.IsStartOfComment() && strings.IndexByte(HoconNotInUnquotedText, p.Peek()) == -1
}

func (p *HoconTokenizer) PullSimpleValue() *Token {
	if p.IsSpaceOrTab() {
		return p.PullSpaceOrTab()
	}

	if p.isUnquotedText() {
		return p.pullUnquotedText()
	}
	panic("No simple value found")
}

func (p *HoconTokenizer) isValue() bool {

	if p.IsArrayStart() ||
		p.IsObjectStart() ||
		p.IsStartOfTripleQuotedText() ||
		p.IsSubstitutionStart() ||
		p.IsStartOfQuotedText() ||
		p.isUnquotedText() {
		return true
	}
	return false
}

/*
SPACE (\u0020)
NO-BREAK SPACE (\u00A0)
OGHAM SPACE MARK (\u1680)
EN QUAD (\u2000)
EM QUAD (\u2001)
EN SPACE (\u2002)
EM SPACE (\u2003)
THREE-PER-EM SPACE (\u2004)
FOUR-PER-EM SPACE (\u2005)
SIX-PER-EM SPACE (\u2006)
FIGURE SPACE (\u2007)
PUNCTUATION SPACE (\u2008)
THIN SPACE (\u2009)
HAIR SPACE (\u200A)
NARROW NO-BREAK SPACE (\u202F)
MEDIUM MATHEMATICAL SPACE (\u205F)
and IDEOGRAPHIC SPACE (\u3000)
Byte Order Mark (\uFEFF)
*/
func isWhitespace(c byte) bool {
	str := string(c)

	switch str {
	case " ", "\t", "\n", "\u000B", "\u000C",
		"\u000D", "\u00A0", "\u1680", "\u2000",
		"\u2001", "\u2002", "\u2003", "\u2004",
		"\u2005", "\u2006", "\u2007", "\u2008",
		"\u2009", "\u200A", "\u202F", "\u205F",
		"\u2060", "\u3000", "\uFEFF":
		return true
	}
	return false
}
