package hocon

type TokenType int

const (
	TokenTypeNone TokenType = iota
	TokenTypeComment
	TokenTypeKey
	TokenTypeLiteralValue
	TokenTypeAssign
	TokenTypePlusAssign
	TokenTypeObjectStart
	TokenTypeObjectEnd
	TokenTypeDot
	TokenTypeNewline
	TokenTypeEoF
	TokenTypeArrayStart
	TokenTypeArrayEnd
	TokenTypeComma
	TokenTypeSubstitute
	TokenTypeInclude
)

var (
	DefaultToken = Token{}
)

type Token struct {
	tokenType  TokenType
	value      string
	isOptional bool
}

func NewToken(v interface{}) *Token {

	switch value := v.(type) {
	case string:
		{
			return &Token{tokenType: TokenTypeLiteralValue, value: value}
		}
	case TokenType:
		{
			return &Token{tokenType: value}
		}
	}

	return nil
}

func (p *Token) Key(key string) *Token {
	return &Token{tokenType: TokenTypeKey, value: key}
}

func (p *Token) Substitution(path string, isOptional bool) *Token {
	return &Token{tokenType: TokenTypeSubstitute, value: path, isOptional: isOptional}
}

func (p *Token) LiteralValue(value string) *Token {
	return &Token{tokenType: TokenTypeLiteralValue, value: value}
}

func (p *Token) Include(path string) *Token {
	return &Token{tokenType: TokenTypeInclude, value: path}
}

func StringTokenType(tokenType TokenType) string {
	switch tokenType {
	case TokenTypeNone:
		return "TokenTypeNone"
	case TokenTypeComment:
		return "TokenTypeComment"
	case TokenTypeKey:
		return "TokenTypeKey"
	case TokenTypeLiteralValue:
		return "TokenTypeLiteralValue"
	case TokenTypeAssign:
		return "TokenTypeAssign"
	case TokenTypePlusAssign:
		return "TokenTypePlusAssign"
	case TokenTypeObjectStart:
		return "TokenTypeObjectStart"
	case TokenTypeObjectEnd:
		return "TokenTypeObjectEnd"
	case TokenTypeDot:
		return "TokenTypeDot"
	case TokenTypeNewline:
		return "TokenTypeNewline"
	case TokenTypeEoF:
		return "TokenTypeEoF"
	case TokenTypeArrayStart:
		return "TokenTypeArrayStart"
	case TokenTypeArrayEnd:
		return "TokenTypeArrayEnd"
	case TokenTypeComma:
		return "TokenTypeComma"
	case TokenTypeSubstitute:
		return "TokenTypeSubstitute"
	case TokenTypeInclude:
		return "TokenTypeInclude"
	}
	return "<<unknown token type>>"
}
