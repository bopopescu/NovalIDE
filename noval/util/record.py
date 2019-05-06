class Record:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def update(self, e, **kw):
        self.__dict__.update(e, **kw)

    def setdefault(self, **kw):
        "updates those fields that are not yet present (similar to dict.setdefault)"
        for key in kw:
            if not hasattr(self, key):
                setattr(self, key, kw[key])

    def get(self, key, default=None):
        return self.__dict__.get(key, default)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __delitem__(self, key):
        self.__dict__.__delitem__(key)

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __contains__(self, key):
        return key in self.__dict__

    def __repr__(self):
        keys = self.__dict__.keys()
        items = ("{}={!r}".format(k, self.__dict__[k]) for k in keys)
        return "{}({})".format(self.__class__.__name__, ", ".join(items))

    def __str__(self):
        keys = sorted(self.__dict__.keys())
        items = ("{}={!r}".format(k, str(self.__dict__[k])) for k in keys)
        return "{}({})".format(self.__class__.__name__, ", ".join(items))

    def __eq__(self, other):
        # pylint: disable=unidiomatic-typecheck

        if type(self) != type(other):
            return False

        if len(self.__dict__) != len(other.__dict__):
            return False

        for key in self.__dict__:
            if not hasattr(other, key):
                return False
            self_value = getattr(self, key)
            other_value = getattr(other, key)

            if type(self_value) != type(other_value) or self_value != other_value:
                return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(repr(self))
