

def get_model_name(model_class):
    db_name = model_class._meta['use_db']
    return f"{db_name}.{model_class._meta['db_table']}"
