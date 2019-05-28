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
