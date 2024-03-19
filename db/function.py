


class QueryFunction:
    name = ""
    column_as = None

    def __init__(self, column, column_as=None):
        self.field = column
        self.column_as = column_as

    def str(self, m="`"):
        res = f'{self.name}({m}{self.field}{m}) '
        if self.column_as:
            res += f' AS {self.column_as}'
        return res

    def __str__(self):
        if self.column_as:
            return self.column_as
        else:
            return f'{self.name}({self.field}) '

    def __repr__(self):
        return str(self)


class Count(QueryFunction):
    name = "count"

    def str(self, m="`"):
        if self.field == '*':
            res = 'count(*)'
        else:
            res = f'{self.name}({m}{self.field}{m}) '
        if self.column_as:
            res += f' AS {self.column_as}'
        return res


class Sum(QueryFunction):
    name = "sum"

    def __init__(self, column, column_as=None, null_value=None):
        super().__init__(column, column_as)
        self.null_value = null_value

    def str(self, m="`"):
        """
        IFNULL(SUM(`{}`), 0) AS `{}`".format(v, k)
        """
        if self.null_value is None:
            return super().str(m)

        res = f'IFNULL({self.name}({m}{self.field}{m}), {self.null_value}) '
        if self.column_as:
            res += f' AS {self.column_as}'
        return res
