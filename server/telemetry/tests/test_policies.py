from telemetry.policies import vendor_cost_micros


def test_vendor_cost_sums_input_and_output():
    assert vendor_cost_micros(1000, 1000, 140, 280) == 420


def test_vendor_cost_scales_linearly():
    assert vendor_cost_micros(2000, 0, 140, 280) == 280
    assert vendor_cost_micros(0, 2000, 140, 280) == 560


def test_vendor_cost_handles_none():
    assert vendor_cost_micros(None, None, 140, 280) == 0


def test_vendor_cost_rounds_up():
    assert vendor_cost_micros(1, 0, 140, 280) == 1
