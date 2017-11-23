package hocon

type MightBeAHoconObject interface {
	IsObject() bool
	GetObject() *HoconObject
}

type HoconElement interface {
	IsString() bool
	GetString() string
	IsArray() bool
	GetArray() []*HoconValue
}
