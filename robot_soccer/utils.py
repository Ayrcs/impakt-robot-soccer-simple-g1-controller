def clamp(value: float, min: float, max: float) -> float:
    if value > max:
        return max
    if value < min:
        return min
    return value