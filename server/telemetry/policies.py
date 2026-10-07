import math


def vendor_cost_micros(
    tokens_in,
    tokens_out,
    input_per_1k_micros,
    output_per_1k_micros,
):
    cost = (
        (tokens_in or 0) / 1000 * input_per_1k_micros
        + (tokens_out or 0) / 1000 * output_per_1k_micros
    )
    return math.ceil(cost)
