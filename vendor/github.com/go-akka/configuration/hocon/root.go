package hocon

type HoconRoot struct {
	value         *HoconValue
	substitutions []*HoconSubstitution
}

func NewHoconRoot(value *HoconValue, substitutions ...*HoconSubstitution) *HoconRoot {
	return &HoconRoot{
		value:         value,
		substitutions: substitutions,
	}
}

func (p HoconRoot) Value() *HoconValue {
	return p.value
}

func (p HoconRoot) Substitutions() []*HoconSubstitution {
	return p.substitutions
}
