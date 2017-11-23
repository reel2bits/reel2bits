package logrus_mate

import (
	"github.com/go-akka/configuration"
)

type HOCONConfiguration struct {
	*configuration.Config
}

func NewConfiguration(conf *configuration.Config) Configuration {
	return &HOCONConfiguration{
		conf,
	}
}

func (p *HOCONConfiguration) GetConfig(path string) Configuration {
	conf := p.Config.GetConfig(path)
	if conf == nil {
		return nil
	}
	return &HOCONConfiguration{conf}
}

func (p *HOCONConfiguration) WithFallback(fallback Configuration) {
	p.Config.WithFallback(fallback.(*HOCONConfiguration).Config)
}

func (p *HOCONConfiguration) Keys() []string {
	return p.Config.Root().GetObject().GetKeys()
}

type HOCONConfigProvider struct {
}

func (p *HOCONConfigProvider) LoadConfig(filename string) Configuration {
	conf := configuration.LoadConfig(filename)
	return NewConfiguration(conf)
}

func (p *HOCONConfigProvider) ParseString(cfgStr string) Configuration {
	conf := configuration.ParseString(cfgStr)
	return NewConfiguration(conf)
}
