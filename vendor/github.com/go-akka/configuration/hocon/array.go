package hocon

import (
	"strings"
)

type HoconArray struct {
	values []*HoconValue
}

func NewHoconArray() *HoconArray {
	return &HoconArray{}
}

func (p *HoconArray) IsString() bool {
	return false
}

func (p *HoconArray) GetString() string {
	panic("This element is an array and not a string.")
}

func (p *HoconArray) IsArray() bool {
	return true
}

func (p *HoconArray) GetArray() []*HoconValue {
	return p.values
}

func (p *HoconArray) String() string {
	var strs []string
	for _, v := range p.values {
		strs = append(strs, v.String())
	}
	return "[" + strings.Join(strs, ",") + "]"
}
