from torch2pc_thesis.config import resolve_config


def test_all_primary_methods_resolve() -> None:
    for method in ["bp", "exact", "fixedpred", "strict"]:
        config = resolve_config("configs", stage="smoke", method=method)
        assert config["method"]["name"] == method
