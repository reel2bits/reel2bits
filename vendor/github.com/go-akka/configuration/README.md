HOCON (Human-Optimized Config Object Notation)
=====

[HOCON Docs](https://github.com/typesafehub/config/blob/master/HOCON.md).

> Currently, some features are not implemented, the API might be a little changed in the future.


`example.go`

```go
package main

import (
  "fmt"
  "github.com/go-akka/configuration"
)

var configText = `
####################################
# Typesafe HOCON                   #
####################################

config {
  # Comment
  version = "0.0.1"
  one-second = 1s
  one-day = 1day
  array = ["one", "two", "three"] #comment
  bar = "bar"
  foo = foo.${config.bar} 
  number = 1
  object {
    a = "a"
    b = "b"
    c = {
            d = ${config.object.a} //comment
        }
    }
}
// fallback
config.object.a="newA"
config.object.c.f="valueF"

// self reference
self-ref=1
self-ref=[${self-ref}][2]

// byte size
byte-size=10MiB

// system envs
home:${HOME}

plus-equal=foo
plus-equal+=bar

plus-equal-array=[foo]
plus-equal-array+=[bar, ${HOME}]
`

func main() {
  conf := configuration.ParseString(configText)

  fmt.Println("config.one-second:", conf.GetTimeDuration("config.one-second"))
  fmt.Println("config.one-day:", conf.GetTimeDuration("config.one-day"))
  fmt.Println("config.array:", conf.GetStringList("config.array"))
  fmt.Println("config.bar:", conf.GetString("config.bar"))
  fmt.Println("config.foo:", conf.GetString("config.foo"))
  fmt.Println("config.number:", conf.GetInt64("config.number"))
  fmt.Println("config.object.a:", conf.GetString("config.object.a"))
  fmt.Println("config.object.c.d:", conf.GetString("config.object.c.d"))
  fmt.Println("config.object.c.f:", conf.GetString("config.object.c.f"))
  fmt.Println("self-ref:", conf.GetInt64List("self-ref"))
  fmt.Println("byte-size:", conf.GetByteSize("byte-size"))
  fmt.Println("home:", conf.GetString("home"))
  fmt.Println("default:", conf.GetString("none", "default-value"))
  fmt.Println("plus-equal:", conf.GetString("plus-equal"))
  fmt.Println("plus-equal-array:", conf.GetStringList("plus-equal-array"))
}

```

```bash
> go run example.go
config.one-second: 1s
config.one-day: 24h0m0s
config.array: [one two three]
config.bar: bar
config.foo: foo.bar
config.number: 1
config.object.a: newA
config.object.c.d: a
config.object.c.f: valueF
self-ref: [1 2]
byte-size: 10485760
home: /Users/zeal
default: default-value
plus-equal: foobar
plus-equal-array: [foo bar /Users/zeal]
```
