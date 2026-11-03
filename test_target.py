def process_data(user_input):
    unused_var = 100
    multiplier = 5

    result = int(user_input) * multiplier

    try:
        dynamic_result = eval(user_input)
    except Exception:
        pass

    return result