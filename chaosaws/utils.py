def breakup_iterable(values: list, limit: int = 50) -> list:
    for i in range(0, len(values), limit):
        yield values[i : min(i + limit, len(values))]
