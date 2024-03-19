def model_format(dataset, columns, model_class, joins=None):
    res = []
    for rows in dataset:
        d = dict(zip(columns, rows))
        pk = d[model_class._meta['primary_key']]
        d = model_class.load(**d)
        d.instance = pk

        idx = len(columns)
        for join in joins:
            _d = dict(zip(join.columns, rows[idx:]))
            _pk = _d[join.model_class._meta['primary_key']]
            if _pk is None:
                _d = None
            else:
                _d = join.model_class(**_d)
                _d.instance = _pk
            setattr(d, join.link_name, _d)
            idx += len(join.columns)

        res.append(d)

    return res



def dict_format(dataset, columns, joins=None):
    res = []
    for rows in dataset:
        _columns = [str(s) for s in columns]
        d = dict(zip(_columns, rows))
        idx = len(_columns)
        for join in joins:
            _join_columns = [str(s) for s in join.columns]
            _d = dict(zip(_join_columns, rows[idx:]))
            d[join.link_name] = _d
            idx += len(_join_columns)
        res.append(d)

    return res
