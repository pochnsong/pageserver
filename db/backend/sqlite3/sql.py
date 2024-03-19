from pageserver.db.fields import *
__all__ = ["SQL"]


def CONSTRAINT(field):
    res = ""
    if not field.attrs["nullable"]:
        res += " NOT NULL"
    if field.attrs["unique"]:
        res += " UNIQUE"

    if field.attrs["primary_key"]:
        res += " PRIMARY KEY"

    return res


def DEFAULT(field, wrapper=''):
    if (v := field.attrs["default"]) is not None:
        if not callable(v):
            return f" DEFAULT {wrapper}{v}{wrapper}"
    return ''


def TEXT(field):
    max_length = field.attrs['max_length']
    res = f"TEXT({max_length})" if max_length else "TEXT"
    return res+CONSTRAINT(field)


def INT(field):
    res = "INTEGER"

    res += DEFAULT(field)
    res += CONSTRAINT(field)
    if field.attrs.get('auto_increment'):
        res += " AUTOINCREMENT"

    return res


def REAL(field):
    res = "REAL"

    if v := field.attrs['default']:
        res += f" DEFAULT {v}"
    return res+CONSTRAINT(field)


def BOOL(field):
    res = "BOOLEAN"

    if (v := field.attrs["default"]) is not None:
        if not callable(v):
            res += f" DEFAULT {'true' if v else 'false'}"

    res += CONSTRAINT(field)

    return res


def DATE(field):
    res = "DATE"
    res += DEFAULT(field)
    return res+CONSTRAINT(field)

def DATETIME(field):
    res = "DATETIME"
    res += DEFAULT(field)
    return res+CONSTRAINT(field)


MAPPING = [
    [TextField, TEXT],
    [CharField, TEXT],
    [VarCharField, TEXT],
    [TinyIntField, INT],
    [IntegerField, INT],
    [BigIntegerField, INT],
    [FloatField, REAL],
    [DoubleField, REAL],
    [DateField, DATE],
    [DateTimeField, DATETIME],
    [BoolField, BOOL],
]


class SQL:
    @classmethod
    def field(cls, field):
        for f in MAPPING:
            if isinstance(field, f[0]):
                return f[1](field)

        raise Exception("unknown field {}".format(field))
