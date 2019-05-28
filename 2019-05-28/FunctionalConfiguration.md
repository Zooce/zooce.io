# Functional Configuration
> Tuesday, May 28th 2019 - 8:37 AM

This morning I was looking for some information on design patterns in Go (golang), and found a great talk by Edward Muller at Gophercon 2017 titled, ["Go Anti-Patterns."](https://youtu.be/ltqV6pDKZD8) In that talk he mentions a common \[anti-\]pattern whereby a struct's configurable fields are configured by giving the user a configuration struct to fill out and pass around. He says the main problems with this design choice is that the configuration struct can, over time, become very large and most of its fields aren't even used most functions it's passed to. This creates all kinds of problems:
- What about default values?
- What about zero values? Will these ever conflict with default values?
- If I pass the configuration struct to other functions, how will I know which fields those functions actually care about?

```go
// https://play.golang.org/p/M4xSC4EUrH9
package main

import "fmt"

type Config struct {
	Foo int
	Bar string
}

type Thing struct {
	Foo int
	Bar string
}

func NewThing(c Config) *Thing {
	return &Thing{
		Foo: c.Foo,
		Bar: c.Bar,
	}
}

func main() {
	c := Config{Foo: 13, Bar: "awesome"}
	t := NewThing(c)

	fmt.Printf("%+v\n", t)
}
```

## Alternatives

One alternative is to simply create separate factory functions for each permutation of configuration values. By the time you're reading this sentence, you should already be cringing. If you take this approach, what happens when your config has 15 fields? How many permutations is that? `15! + 1 = 1,307,674,368,001` Um...okay not a good idea. Also, this still doesn't deal very nicely with default values.

```go
// https://play.golang.org/p/lwC8wkQ3htN
package main

import "fmt"

type Thing struct {
	Foo int
	Bar string
}

func NewThing() *Thing {
	return &Thing{} // could put default values here, maybe
}

func NewFooThing(f int) *Thing {
	return &Thing{Foo: f}
}

func NewBarThing(b string) *Thing {
	return &Thing{Bar: b}
}

func NewFooBarThing(f int, b string) *Thing {
	return &Thing{Foo: f, Bar: b}
}

func main() {
	t1 := NewThing()
	t2 := NewFooThing(13)
	t3 := NewBarThing("awesome")
	t4 := NewFooBarThing(13, "awesome")

	ts := []*Thing{t1, t2, t3, t4}
	for _, t := range ts {
		fmt.Printf("%+v\n", t)
	}
}
```

## The Functional Way

We can do a lot better. Instead of providing a config struct or specific factory functions, let's provide some configuration functions.

> _Muller gives credit to Dave Cheney's blog post, ["Functional options for friendly APIs"](http://bit.ly/GoFunctionalConfig) who in-turn gives credit to Rob Pike's blog post, ["Self-referential functions and the design of options"](http://commandcenter.blogspot.com.au/2014/01/self-referential-functions-and-design.html)._

```go
// https://play.golang.org/p/WXvvvdVRLUC
package main

import "fmt"

type Thing struct {
	Foo int
	Bar string
}

func FooConfig(f int) func(*Thing) {
	return func(t *Thing) {
		t.Foo = f
	}
}

func BarConfig(b string) func(*Thing) {
	return func(t *Thing) {
		t.Bar = b
	}
}

func NewThing(configs ...func(*Thing)) *Thing {
	t := Thing{}
	for _, config := range configs {
		config(&t)
	}
	return &t
}

func main() {
	t1 := NewThing()
	t2 := NewThing(FooConfig(13))
	t3 := NewThing(BarConfig("awesome"))
	t4 := NewThing(FooConfig(13), BarConfig("awesome"))
	t5 := NewThing(BarConfig("awesome"), FooConfig(13))

	ts := []*Thing{t1, t2, t3, t4, t5}
	for _, t := range ts {
		fmt.Printf("%+v\n", t)
	}
}
```

This is really cool! It also got me thinking about doing this other languages. Let's try:

### Python

I can do this same thing in Python:

```python
class Thing:
    def __init__(self, *configs):
        self.Foo = 0
        self.Bar = ""
        for config in configs:
            config(self)

    def __repr__(self):
        # an f-string would be nicer here, but it requires you run this with Python 3
        # return f"Foo: {self.Foo}, Bar: {self.Bar}"
        return "Foo: {}, Bar: {}".format(self.Foo, self.Bar)

def foo_config(f):
    def config(t):
        t.Foo = f
    return config

def bar_config(b):
    def config(t):
        t.Bar = b
    return config

if __name__ == "__main__":
    t1 = Thing()
    t2 = Thing(foo_config(13))
    t3 = Thing(bar_config("awesome"))
    t4 = Thing(foo_config(13), bar_config("awesome"))
    t5 = Thing(bar_config("awesome"), foo_config(13))

    ts = [t1, t2, t3, t4, t5]
    for t in ts:
        print(t)
```

### C++

I think we can also do something similar in C++, although I could not figure out way to do this with variadic parameters, because apparently the `va_arg` macro can't convert 'non-POD' arguments (like a function pointer). Here's a relatively close approximation I came up with in C++11:

```cpp
// https://repl.it/@Zooce/Functional-Configuration
#include <iostream>
#include <string>
#include <functional>
#include <vector>

struct Thing {
    int Foo{0};
    std::string Bar{};
};

typedef std::function<void (Thing*)> ConfigFn;

ConfigFn FooConfig(int f) {
    return [f](Thing* t) {
        t->Foo = f;
    };
}

ConfigFn BarConfig(std::string b) {
    return [b](Thing* t) {
        t->Bar = b;
    };
}

Thing* NewThing(std::vector<ConfigFn>* configs = nullptr)
{
    Thing* t = new Thing();

    if(configs != nullptr) {
        for(int i = 0; i < configs->size(); ++i) {
            ConfigFn config = (*configs)[i];
            config(t);
        }
    }

    return t;
}

int main() {
    Thing* t1 = NewThing();

    std::vector<ConfigFn> configs2{FooConfig(13)};
    Thing* t2 = NewThing(&configs2);

    std::vector<ConfigFn> configs3{BarConfig("awesome")};
    Thing* t3 = NewThing(&configs3);

    std::vector<ConfigFn> configs4{FooConfig(13), BarConfig("awesome")};
    Thing* t4 = NewThing(&configs4);

    std::vector<ConfigFn> configs5{BarConfig("awesome"), FooConfig(13)};
    Thing* t5 = NewThing(&configs5);

    Thing* ts[5] = {t1, t2, t3, t4, t5};
    for(int i = 0; i < 5; ++i) {
        Thing* t = ts[i];
        std::cout << t;
        std::cout << " {Foo: " << t->Foo;
        std::cout << ", Bar: " << t->Bar;
        std::cout << "}" << std::endl;

        delete t; t = nullptr;
    }
    return 0;
}
```
