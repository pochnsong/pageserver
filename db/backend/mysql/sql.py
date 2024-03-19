from pageserver.db.fields import *
__all__ = ["SQL"]


def CONSTRAINT(field):
    res = ""
    if not field.attrs["nullable"]:
        res += " NOT NULL"

    if field.attrs["primary_key"]:
        res += " PRIMARY KEY"

    return res


def DEFAULT(field, wrapper=''):
    default_value = field.attrs["default"]
    if default_value is not None:
        if not callable(default_value):
            return f" DEFAULT {wrapper}{default_value}{wrapper}"
    return ''


def VARCHAR(field):
    max_length = field.attrs['max_length']
    res = f"VARCHAR({max_length})"
    res += DEFAULT(field, "'")
    return res+CONSTRAINT(field)

def CHAR(field):
    max_length = field.attrs['max_length']
    res = f"CHAR({max_length})"
    res += DEFAULT(field, "'")
    return res+CONSTRAINT(field)

def TEXT(field):
    max_length = field.attrs['max_length']
    res = f"TEXT({max_length})" if max_length else "TEXT"
    return res+CONSTRAINT(field)


def INT1(field):
    res = "TINYINT"
    res += DEFAULT(field)
    return res+CONSTRAINT(field)


def INT(field):
    res = "INT"
    if field.attrs.get('auto_increment'):
        res += " AUTO_INCREMENT"

    res += DEFAULT(field)
    return res+CONSTRAINT(field)


def BIGINT(field):
    res = "BIGINT"
    if field.attrs.get('auto_increment'):
        res += " AUTO_INCREMENT"

    res += DEFAULT(field)
    return res+CONSTRAINT(field)


def FLOAT(field):
    res = "FLOAT"
    res += DEFAULT(field)
    return res+CONSTRAINT(field)


def DOUBLE(field):
    res = "DOUBLE"
    res += DEFAULT(field)
    return res+CONSTRAINT(field)


def DATE(field):
    res = "DATE"
    res += DEFAULT(field)
    return res+CONSTRAINT(field)

def DATETIME(field):
    res = "DATETIME"
    res += DEFAULT(field)
    return res+CONSTRAINT(field)


def BOOL(field):
    res = "BOOLEAN"

    if (v := field.attrs["default"]) is not None:
        if not callable(v):
            res += f" DEFAULT {'true' if v else 'false'}"

    res += CONSTRAINT(field)

    return res


MAPPING = [
    [TextField, TEXT],
    [CharField, CHAR],
    [VarCharField, VARCHAR],
    [BigIntegerField, BIGINT],
    [IntegerField, INT],
    [TinyIntField, INT1],
    [DoubleField, DOUBLE],
    [FloatField, FLOAT],
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
