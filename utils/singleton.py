def singleton(func):
    instance = None

    def get_instance(*args, **kwargs):
        nonlocal instance
        if instance is None:
            instance = func(*args, **kwargs)
        return instance

    return get_instance