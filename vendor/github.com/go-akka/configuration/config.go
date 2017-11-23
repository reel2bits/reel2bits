package configuration

import (
	"math/big"
	"strings"
	"time"

	"github.com/go-akka/configuration/hocon"
)

type Config struct {
	root          *hocon.HoconValue
	substitutions []*hocon.HoconSubstitution
	fallback      *Config
}

func NewConfigFromRoot(root *hocon.HoconRoot) *Config {
	if root.Value() == nil {
		panic("The root value cannot be null.")
	}

	return &Config{
		root:          root.Value(),
		substitutions: root.Substitutions(),
	}
}

func NewConfigFromConfig(source, fallback *Config) *Config {
	if source == nil {
		panic("The source configuration cannot be null.")
	}

	return &Config{
		root:     source.root,
		fallback: fallback,
	}
}

func (p *Config) IsEmpty() bool {
	return p.root == nil || p.root.IsEmpty()
}

func (p *Config) Root() *hocon.HoconValue {
	return p.root
}

func (p *Config) Copy() *Config {

	var fallback *Config
	if p.fallback != nil {
		fallback = p.fallback.Copy()
	}
	return &Config{
		fallback:      fallback,
		root:          p.root,
		substitutions: p.substitutions,
	}
}

func (p *Config) GetNode(path string) *hocon.HoconValue {
	elements := splitDottedPathHonouringQuotes(path)
	currentNode := p.root

	if currentNode == nil {
		panic("Current node should not be null")
	}

	for _, key := range elements {
		currentNode = currentNode.GetChildObject(key)
		if currentNode == nil {
			if p.fallback != nil {
				return p.fallback.GetNode(path)
			}
			return nil
		}
	}
	return currentNode
}

func (p *Config) GetBoolean(path string, defaultVal ...bool) bool {
	obj := p.GetNode(path)
	if obj := p.GetNode(path); obj == nil {
		if len(defaultVal) > 0 {
			return defaultVal[0]
		}
		return false
	}
	return obj.GetBoolean()
}

func (p *Config) GetByteSize(path string) *big.Int {
	obj := p.GetNode(path)
	if obj == nil {
		return big.NewInt(-1)
	}
	return obj.GetByteSize()
}

func (p *Config) GetInt32(path string, defaultVal ...int32) int32 {
	obj := p.GetNode(path)
	if obj := p.GetNode(path); obj == nil {
		if len(defaultVal) > 0 {
			return defaultVal[0]
		}
		return 0
	}
	return obj.GetInt32()
}

func (p *Config) GetInt64(path string, defaultVal ...int64) int64 {
	obj := p.GetNode(path)
	if obj := p.GetNode(path); obj == nil {
		if len(defaultVal) > 0 {
			return defaultVal[0]
		}
		return 0
	}
	return obj.GetInt64()
}

func (p *Config) GetString(path string, defaultVal ...string) string {
	obj := p.GetNode(path)
	if obj := p.GetNode(path); obj == nil {
		if len(defaultVal) > 0 {
			return defaultVal[0]
		}
		return ""
	}
	return obj.GetString()
}

func (p *Config) GetFloat32(path string, defaultVal ...float32) float32 {
	obj := p.GetNode(path)
	if obj := p.GetNode(path); obj == nil {
		if len(defaultVal) > 0 {
			return defaultVal[0]
		}
	}
	return obj.GetFloat32()
}

func (p *Config) GetFloat64(path string, defaultVal ...float64) float64 {
	obj := p.GetNode(path)
	if obj := p.GetNode(path); obj == nil {
		if len(defaultVal) > 0 {
			return defaultVal[0]
		}
		return 0
	}
	return obj.GetFloat64()
}

func (p *Config) GetTimeDuration(path string, defaultVal ...time.Duration) time.Duration {
	obj := p.GetNode(path)
	if obj := p.GetNode(path); obj == nil {
		if len(defaultVal) > 0 {
			return defaultVal[0]
		}
		return 0
	}
	return obj.GetTimeDuration(true)
}

func (p *Config) GetTimeDurationInfiniteNotAllowed(path string, defaultVal ...time.Duration) time.Duration {
	obj := p.GetNode(path)
	if obj := p.GetNode(path); obj == nil {
		if len(defaultVal) > 0 {
			return defaultVal[0]
		}
		return 0
	}
	return obj.GetTimeDuration(false)
}

func (p *Config) GetBooleanList(path string) []bool {
	obj := p.GetNode(path)
	if obj := p.GetNode(path); obj == nil {
		return nil
	}
	return obj.GetBooleanList()
}

func (p *Config) GetFloat32List(path string) []float32 {
	obj := p.GetNode(path)
	if obj := p.GetNode(path); obj == nil {
		return nil
	}
	return obj.GetFloat32List()
}

func (p *Config) GetFloat64List(path string) []float64 {
	obj := p.GetNode(path)
	if obj := p.GetNode(path); obj == nil {
		return nil
	}
	return obj.GetFloat64List()
}

func (p *Config) GetInt32List(path string) []int32 {
	obj := p.GetNode(path)
	if obj := p.GetNode(path); obj == nil {
		return nil
	}
	return obj.GetInt32List()
}

func (p *Config) GetInt64List(path string) []int64 {
	obj := p.GetNode(path)
	if obj := p.GetNode(path); obj == nil {
		return nil
	}
	return obj.GetInt64List()
}

func (p *Config) GetByteList(path string) []byte {
	obj := p.GetNode(path)
	if obj := p.GetNode(path); obj == nil {
		return nil
	}
	return obj.GetByteList()
}

func (p *Config) GetStringList(path string) []string {
	obj := p.GetNode(path)
	if obj := p.GetNode(path); obj == nil {
		return nil
	}
	return obj.GetStringList()
}

func (p *Config) GetConfig(path string) *Config {
	value := p.GetNode(path)
	if p.fallback != nil {
		f := p.fallback.GetConfig(path)
		if value == nil && f == nil {
			return nil
		}
		if value == nil {
			return f
		}
		return NewConfigFromRoot(hocon.NewHoconRoot(value)).WithFallback(f)
	}

	if value == nil {
		return nil
	}
	return NewConfigFromRoot(hocon.NewHoconRoot(value))
}

func (p *Config) GetValue(path string) *hocon.HoconValue {
	return p.GetNode(path)
}

func (p *Config) WithFallback(fallback *Config) *Config {
	if fallback == p {
		panic("Config can not have itself as fallback")
	}

	clone := p.Copy()
	current := clone
	for current.fallback != nil {
		current = current.fallback
	}
	current.fallback = fallback
	return clone
}

func (p *Config) HasPath(path string) bool {
	return p.GetNode(path) != nil
}

func (p *Config) AddConfig(textConfig string, fallbackConfig *Config) *Config {
	root := hocon.Parse(textConfig, nil)
	config := NewConfigFromRoot(root)
	return config.WithFallback(fallbackConfig)
}

func (p *Config) AddConfigWithTextFallback(config *Config, textFallback string) *Config {
	fallbackRoot := hocon.Parse(textFallback, nil)
	fallbackConfig := NewConfigFromRoot(fallbackRoot)
	return config.WithFallback(fallbackConfig)
}

func (p Config) String() string {
	return p.root.String()
}

func splitDottedPathHonouringQuotes(path string) []string {
	tmp1 := strings.Split(path, "\"")
	var values []string
	for i := 0; i < len(tmp1); i++ {
		tmp2 := strings.Split(tmp1[i], ".")
		for j := 0; j < len(tmp2); j++ {
			if len(tmp2[j]) > 0 {
				values = append(values, tmp2[j])
			}
		}
	}
	return values
}
