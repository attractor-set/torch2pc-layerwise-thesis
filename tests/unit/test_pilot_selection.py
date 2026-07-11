from scripts.select_pilot import experiment_key, primary_attempts


def _event(run_id: str, status: str, started: str) -> dict[str, str]:
    return {
        "run_id": run_id,
        "experiment_id": "exp-1",
        "status": status,
        "stage": "pilot",
        "dataset": "FashionMNIST",
        "model": "lenet_classic",
        "method": "strict",
        "model_seed": "40",
        "eta": "0.05",
        "inference_steps": "20",
        "started_utc": started,
    }


def test_first_terminal_attempt_defines_pilot_success_cell() -> None:
    failure = _event("run-a", "failed", "2026-07-10T00:00:00Z")
    success = _event("run-b", "completed", "2026-07-10T01:00:00Z")
    selected = primary_attempts([success, failure])
    assert selected[experiment_key(failure)]["status"] == "failed"
