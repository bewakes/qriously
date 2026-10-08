import math


def vendor_cost_micros(
    tokens_in: int | None,
    tokens_out: int | None,
    input_per_1k_micros: int,
    output_per_1k_micros: int,
) -> int:
    cost = (
        (tokens_in or 0) / 1000 * input_per_1k_micros
        + (tokens_out or 0) / 1000 * output_per_1k_micros
    )
    return math.ceil(cost)
