import torch

from torch2pc_thesis.robustness import corrupt_batch


def test_gaussian_blur_spreads_an_impulse() -> None:
    inputs = torch.zeros((1, 1, 9, 9), dtype=torch.float32)
    inputs[0, 0, 4, 4] = 1.0
    blurred = corrupt_batch(inputs, "gaussian_blur", 3, seed=1)
    assert 0.0 < float(blurred[0, 0, 4, 4]) < 1.0
    assert float(blurred[0, 0, 4, 3]) > 0.0


def test_stochastic_corruption_is_reproducible_for_same_seed() -> None:
    inputs = torch.full((2, 1, 8, 8), 0.5)
    first = corrupt_batch(inputs, "gaussian_noise", 2, seed=123)
    second = corrupt_batch(inputs, "gaussian_noise", 2, seed=123)
    assert torch.equal(first, second)
