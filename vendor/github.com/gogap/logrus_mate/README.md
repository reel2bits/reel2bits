# Logrus Mate <img src="http://i.imgur.com/hTeVwmJ.png" width="40" height="40" alt=":walrus:" class="emoji" title=":walrus:"/>

**Logrus mate** is a tool for [Logrus](https://github.com/sirupsen/logrus), it will help you to initial logger by config, including `Formatter`, `Hook`，`Level` and `Output` .

> If you more prefer old version, you could checkout tag v1.0.0

#### Example

**Example 1:**

Hijack `logrus.StandardLogger()`

```go
package main

import (
    "github.com/sirupsen/logrus"
    "github.com/gogap/logrus_mate"
)

func main() {
    logrus_mate.Hijack(
        logrus.StandardLogger(),
        logrus_mate.ConfigString(
            `{formatter.name = "json"}`,
        ),
    )
    
    logrus.WithField("Field", "A").Debugln("Hello JSON")
}

```

**Example 2:**

Create new logger from mate:

```go
package main

import (
    "github.com/gogap/logrus_mate"
)

func main() {
    mate, _ := logrus_mate.NewLogrusMate(
        logrus_mate.ConfigString(
            `{ mike {formatter.name = "json"} }`,
        ),
    )
    
    mikeLoger := mate.Logger("mike")
    mikeLoger.Errorln("Hello Error Level from Mike and my formatter is json")
}
```

**Example 3:**

Hi jack logger by mate

```go
package main

import (
    "github.com/sirupsen/logrus"
    "github.com/gogap/logrus_mate"
)

func main() {
    mate, _ := logrus_mate.NewLogrusMate(
        logrus_mate.ConfigString(
            `{ mike {formatter.name = "json"} }`,
        ),
    )

    mate.Hijack(
        logrus.StandardLogger(),
        "mike",
    )
    
    logrus.Println("hello std logger is hijack by mike")
}
```

**Example 4:**

Fallback the ConfigString

```go
package main

import (
    "github.com/sirupsen/logrus"
    "github.com/gogap/logrus_mate"
)

func main() {
    mate, _ := logrus_mate.NewLogrusMate(
        logrus_mate.ConfigString(
            `{ mike {formatter.name = "json"} }`,
        ),
        logrus_mate.ConfigFile(
            "mate.conf", // { mike {formatter.name = "text"} }
        ),
    )

    mate.Hijack(
        logrus.StandardLogger(),
        "mike",
    )
    
    logrus.Println("hello std logger is hijack by mike")
}
```

 **the `json` formatter is used**

**Example 5:**

Fallback config while hijack

```go
package main

import (
    "github.com/sirupsen/logrus"
    "github.com/gogap/logrus_mate"
)

func main() {
    mate, _ := logrus_mate.NewLogrusMate(
        logrus_mate.ConfigFile(
            "mate.conf", // { mike {formatter.name = "text"} }
        ),
    )

    mate.Hijack(logrus.StandardLogger(),
        "mike",
        logrus_mate.ConfigString(
            `{formatter.name = "json"}`,
        ),
    )

    logrus.Errorln("hello std logger is hijack by mike")
}
```

**the `json` formatter is used**

> currently we are using https://github.com/go-akka/configuration for logger config, it will more powerful config format for human read, 
you also could set your own config provider

#### Hooks
| Hook  | Options |
| ----- | ----------- |
| [Airbrake](https://github.com/gemnasium/logrus-airbrake-hook) | `project-id` `api-key` `env`|
| [Syslog](https://github.com/sirupsen/logrus/blob/master/hooks/syslog/syslog.go) | `network` `address` `priority` `tag`|
| [BugSnag](https://github.com/sirupsen/logrus/blob/master/hooks/bugsnag/bugsnag.go) | `api-key` |
| [Slackrus](https://github.com/johntdyer/slackrus) | `url` `levels` `channel` `emoji` `username`|
| [Graylog](https://github.com/gemnasium/logrus-graylog-hook) | `address` `facility` `extra`|
| [Mail](https://github.com/zbindenren/logrus_mail) | `app-name` `host` `port` `from` `to` `username` `password`|
| [Logstash](https://github.com/bshuster-repo/logrus-logstash-hook) | `app-name` `protocol` `address` `always-sent-fields` `prefix`|
| File | `filename` `max-lines` `max-size` `daily` `max-days` `rotate` `level`|
| BearyChat | `url` `levels` `channel` `user` `markdown` `async`|

When we need use above hooks, we need import these package as follow:

```go
import _ "github.com/gogap/logrus_mate/hooks/syslog"
import _ "github.com/gogap/logrus_mate/hooks/mail"
```

If you want write your own hook, you just need todo as follow:

```go
package myhook

import (
    "github.com/gogap/logrus_mate"
)

type MyHookConfig struct {
    Address  string
}

func init() {
    logrus_mate.RegisterHook("myhook", NewMyHook)
}

func NewMyHook(config logrus_mate.Configuration) (hook logrus.Hook, err error) {
    conf := MyHookConfig{}
    if config!=nil {
        conf.Address = config.GetString("address")
    }

    // write your hook logic code here

    return
}
```


#### Formatters

**internal formatters:**

| Formatter  | Options |Output Example |
| ----- | ----------- | ----------- |
|null|||
|text|`force-colors` `disable-colors` `disable-timestamp` `full-timestamp` `timestamp-format` `disable-sorting`|DEBU[0000] Hello Default Logrus Mate|
|json|`timestamp-format`|{"level":"info","msg":"Hello, I am A Logger from jack","time":"2015-10-18T21:24:19+08:00"}|

**3rd formatters:**

| Formatter  | Output Example |
| ----- | ----------- |
|logstash [**Removed**]||

When we need use 3rd formatter, we need import these package as follow:

```go
import _ "github.com/gogap/logrus_mate/formatters/xxx"
```

If you want write your own formatter, you just need todo as follow:

```go
package myformatter

import (
    "github.com/gogap/logrus_mate"
)

type MyFormatterConfig struct {
    Address  string `json:"address"`
}

func init() {
    logrus_mate.RegisterFormatter("myformatter", NewMyFormatter)
}

func NewMyFormatter(config logrus_mate.Configuration) (formatter logrus.Formatter, err error) {
    conf := MyFormatterConfig{}
    if config!=nil {
        conf.Address=config.GetString("address")
    }

    // write your formatter logic code here

    return
}
```

#### Writers

**internal writers (output):**

- stdout
- stderr
- null

**3rd writers:**

| Writer  | Description |
| ----- | ----------- |
|redisio| just for demo, it will output into redis, the key type is list|

When we need use 3rd writer, we need import these package as follow:

```go
import _ "github.com/gogap/logrus_mate/writers/redisio"
```

If you want write your own writer, you just need todo as follow:

```go
package mywriter

import (
    "io"

    "github.com/gogap/logrus_mate"
)

type MyWriterConfig struct {
    Address  string `json:"address"`
}

func init() {
    logrus_mate.RegisterWriter("mywriter", NewMyWriter)
}

func NewMyWriter(config logrus_mate.Configuration) (writer io.Writer, err error) {
    conf := MyWriterConfig{}
    if config!=nil {
        conf.Address=config.GetString("address")
    }

    // write your writer logic code here

    return
}
```

#### Config Provider

The default config provider is `HOCON`, you could use your own config provider, just implement the following interface{}

```go
type ConfigurationProvider interface {
    LoadConfig(filename string) Configuration
    ParseString(cfgStr string) Configuration
}

type Configuration interface {
    GetBoolean(path string, defaultVal ...bool) bool
    GetByteSize(path string) *big.Int
    GetInt32(path string, defaultVal ...int32) int32
    GetInt64(path string, defaultVal ...int64) int64
    GetString(path string, defaultVal ...string) string
    GetFloat32(path string, defaultVal ...float32) float32
    GetFloat64(path string, defaultVal ...float64) float64
    GetTimeDuration(path string, defaultVal ...time.Duration) time.Duration
    GetTimeDurationInfiniteNotAllowed(path string, defaultVal ...time.Duration) time.Duration
    GetBooleanList(path string) []bool
    GetFloat32List(path string) []float32
    GetFloat64List(path string) []float64
    GetInt32List(path string) []int32
    GetInt64List(path string) []int64
    GetByteList(path string) []byte
    GetStringList(path string) []string
    GetConfig(path string) Configuration
    WithFallback(fallback Configuration)
    HasPath(path string) bool
    Keys() []string
}
```

**set your own config provider**

```go
package main

import (
    "github.com/sirupsen/logrus"
    "github.com/gogap/logrus_mate"
)

func main() {
    mate, _ := logrus_mate.NewLogrusMate(
        logrus_mate.ConfigString(
            `{ mike {formatter.name = "json"} }`,
        ),
        logrus_mate.ConfigFile(
            "mate.conf", // { mike {formatter.name = "text"} }
        ),
        logrus_mate.ConfigProvider(
            &logrus_mate.HOCONConfigProvider{}, // this is defualt provider if you did not configurate
        ),
    )

    mate.Hijack(
        logrus.StandardLogger(),
        "mike",
    )
    
    logrus.Println("hello std logger is hijack by mike")
}
```
