from __future__ import annotations

import contextlib
import hashlib
import os
import random
from typing import Any

import numpy as np


def stable_int_seed(*parts: Any) -> int:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "big") % (2**31 - 1)


def configure_threads(torch_threads: int) -> None:
    import torch

    if torch_threads < 1:
        raise ValueError("torch_threads must be positive")
    torch.set_num_threads(torch_threads)
    with contextlib.suppress(RuntimeError):
        torch.set_num_interop_threads(1)


def set_global_seed(
    seed: int,
    deterministic: bool = True,
    *,
    warn_only: bool = False,
) -> None:
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)

    import torch

    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    if deterministic:
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True
        torch.use_deterministic_algorithms(True, warn_only=warn_only)


def seed_worker(worker_id: int) -> None:
    del worker_id
    import torch

    worker_seed = torch.initial_seed() % (2**32)
    np.random.seed(worker_seed)
    random.seed(worker_seed)
