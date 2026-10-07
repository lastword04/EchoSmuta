def plural(n: int, one: str, few: str, many: str) -> str:
    """Русская плюрализация: plural(5, "брикет", "брикета", "брикетов")"""
    n = abs(n) % 100
    d = n % 10
    if 10 < n < 20:
        return many
    if d == 1:
        return one
    if 2 <= d <= 4:
        return few
    return many