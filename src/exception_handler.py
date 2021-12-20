import traceback

def handle_exception(logger):
    def internal_func(func):
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except Exception as e:
                tb_list = traceback.format_exception(None, e, e.__traceback__)

                # Remove 2nd and 3rd element from list (hide decorator usage in traceback)
                for i in range(2):
                    tb_list.pop(1)

                logger.error("Exception occurred:\n" + "".join(tb_list))

        return wrapper
    return internal_func
