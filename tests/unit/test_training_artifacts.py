import numpy as np

from torch2pc_thesis.training import save_predictions


def test_prediction_artifact_preserves_source_indices(tmp_path) -> None:
    path = tmp_path / "predictions.npz"
    evaluation = {
        "y_true": np.array([1, 2]),
        "y_pred": np.array([1, 0]),
        "probabilities": np.array([[0.1, 0.9, 0.0], [0.8, 0.1, 0.1]]),
    }
    save_predictions(path, evaluation, np.array([17, 42]))
    loaded = np.load(path)
    assert loaded["source_index"].tolist() == [17, 42]
    assert loaded["y_true"].tolist() == [1, 2]
