
from datetime import datetime


class Field:

    def __init__(self, name, start, length, out_format):
        self.name = name
        self.start = start
        self.length = length
        self.out_format = out_format
        self.hidden_field = False

    def get_string(self, value):
        out = value.format(out_format)
        if (out.length != length):
            raise RuntimeError("Length for formatted value not correct, expected {exp}, but got {form.length}. (value={val}, formatted={form})".
                               format(exp=self.length, 
                                      form=out,
                                      val=value))
        return out

    def hide(self):
        self.hidden_field = True
        return self

    def is_hidden(self):
        return self.hidden_field

    def get(self):
        return self.value

    def set(self, in_val):
        self.value = in_val

    def parse(self, in_str):
        self.value = in_str

    def format(self):
        return self.out_format.format(self.get())

    def __cmp__(self,other):
        return self.start-other.start

    def __str__(self):
        return self.name+": "+str(self.pretty())

    def pretty(self):
        return self.get();

class IntField(Field):
    def __init__(self, name, start, length):
        Field.__init__(self, name, start, length, "{0:0>"+str(length)+"d}")
        self.value = 0

    def parse(self, in_str):
        try:
            self.value = int(in_str)
        except:
            print "Int field exception"
            print self.name

class StringField(Field):
    def __init__(self, name, start, length):
        Field.__init__(self, name, start, length, "{0: <"+str(length)+"s}")
        self.value = ""

    def get(self):
        return self.value.strip()

    def format(self):
        return self.out_format.format(self.value.encode("iso-8859-1"))

class DateField(Field):
    def __init__(self, name, start):
        Field.__init__(self, name, start, 6, "{0:s}")
        self.value = None

    def parse(self, in_str):
        try:
            self.value = datetime.strptime(in_str,"%d%m%y")
        except:
            self.value = None

    def format(self):
        return self.value.strftime("%d%m%y") if self.value else "000000"

    def pretty(self):
        return self.value.strftime("%d-%m-%Y") if self.value else "(none)"

class LongDateField(Field):
    def __init__(self, name, start):
        Field.__init__(self, name, start, 8, "{0:s}")
        self.value = None

    def parse(self, in_str):
        try:
            self.value = datetime.strptime(in_str,"%d%m%Y")
        except:
            self.value = None

    def format(self):
        return self.value.strftime("%d%m%Y") if self.value else "00000000"

    def pretty(self):
        return self.value.strftime("%d-%m-%Y") if self.value else "(none)"


class FillerField(Field):
    def __init__(self, char, start, length):
        Field.__init__(self, "filler", start, length, "{0:"+char+">"+str(length)+"s}")
        self.hide()
        self.value = ""


class NullableDate():
    def __init__(self, value):
        if (value == "000000"):
            self.date = None
        else:
            self.date = datetime.strptime(value,"%d%m%y")

    def __str__(self):
        return self.date.strftime("%d %B %Y") if self.date else " - "

