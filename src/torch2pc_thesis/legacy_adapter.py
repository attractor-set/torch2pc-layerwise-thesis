from __future__ import annotations

import os
from pathlib import Path

import nbformat
from nbclient import NotebookClient


def execute_legacy_notebook(
    *,
    stage: str,
    notebook_path: str | Path,
    config_path: str | Path,
    output_path: str | Path,
    timeout: int | None = None,
) -> Path:
    source = Path(notebook_path)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    os.environ["RUN_STAGE"] = stage
    os.environ["EXPERIMENT_CONFIG_PATH"] = str(Path(config_path).resolve())
    notebook = nbformat.read(source, as_version=4)  # type: ignore[no-untyped-call]
    client = NotebookClient(
        notebook,
        timeout=timeout,
        kernel_name="python3",
        allow_errors=False,
        resources={"metadata": {"path": str(Path.cwd())}},
    )
    try:
        client.execute()
    finally:
        nbformat.write(notebook, output)  # type: ignore[no-untyped-call]
    return output
