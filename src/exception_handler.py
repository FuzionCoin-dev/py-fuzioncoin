import traceback

def handle_exception(logger):
    def internal_func(func):
        def wrapper(*args, **kwargs):
            try:
                out = func(*args, **kwargs)
            except Exception as e:
                tb_list = traceback.format_exception(None, e, e.__traceback__)
                logger.error("Exception occurred:\n" + "".join(tb_list))

            return out

        return wrapper
    return internal_func
