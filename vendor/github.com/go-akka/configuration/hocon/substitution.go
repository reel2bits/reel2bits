package hocon

import (
	"fmt"
)

type HoconSubstitution struct {
	Path          string
	ResolvedValue *HoconValue
	IsOptional    bool
}

func NewHoconSubstitution(path string, isOptional bool) *HoconSubstitution {
	return &HoconSubstitution{Path: path, IsOptional: isOptional}
}

func (p *HoconSubstitution) IsString() bool {
	if p.ResolvedValue == nil {
		return false
	}
	p.checkCycleRef()
	return p.ResolvedValue.IsString()
}

func (p *HoconSubstitution) GetString() string {
	if p.ResolvedValue == nil {
		return ""
	}
	p.checkCycleRef()
	return p.ResolvedValue.GetString()
}

func (p *HoconSubstitution) IsArray() bool {
	if p.ResolvedValue == nil {
		return false
	}
	p.checkCycleRef()
	return p.ResolvedValue.IsArray()
}
func (p *HoconSubstitution) GetArray() []*HoconValue {
	if p.ResolvedValue == nil {
		return nil
	}
	return p.ResolvedValue.GetArray()
}

func (p *HoconSubstitution) IsObject() bool {
	if p.ResolvedValue == nil {
		return false
	}
	p.checkCycleRef()
	return p.ResolvedValue.IsObject()
}

func (p *HoconSubstitution) GetObject() *HoconObject {
	if p.ResolvedValue == nil {
		return nil
	}
	p.checkCycleRef()
	return p.ResolvedValue.GetObject()
}

func (p *HoconSubstitution) checkCycleRef() {
	if p.hasCycleRef(map[HoconElement]int{}, 1, p.ResolvedValue) {
		panic(fmt.Sprintf("cycle reference in path of %s", p.Path))
	}
}

// Temporary solution
func (p *HoconSubstitution) hasCycleRef(dup map[HoconElement]int, level int, v interface{}) bool {
	if v == nil {
		return false
	}

	val, ok := v.(*HoconValue)
	if val == nil {
		return false
	}

	if !ok {
		return false
	}

	if lvl, exist := dup[val]; exist {
		if lvl != level {
			return true
		}
	}
	dup[val] = level

	for _, subV := range val.values {
		if sub, ok := subV.(*HoconSubstitution); ok {

			if sub.ResolvedValue != nil {
				return p.hasCycleRef(dup, level+1, sub.ResolvedValue)
			}
		}
	}

	return false
}
