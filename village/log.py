def log(message, exception=None):
    if exception is None:
        print(message)
    else:
        print(message, exception)
