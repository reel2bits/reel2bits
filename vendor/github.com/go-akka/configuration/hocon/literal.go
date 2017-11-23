package hocon

type HoconLiteral struct {
	value string
}

func NewHoconLiteral(value string) *HoconLiteral {
	return &HoconLiteral{value: value}
}

func (p *HoconLiteral) IsString() bool {
	return true
}

func (p *HoconLiteral) GetString() string {
	return p.value
}

func (p *HoconLiteral) IsArray() bool {
	return false
}

func (p *HoconLiteral) GetArray() []*HoconValue {
	panic("This element is a string literal and not an array.")
}

func (p *HoconLiteral) String() string {
	return p.value
}
