from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import run_stage3b_a1_eq_s2_container as runner


def test_read_dotenv_parses_reproducibility_values(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    path.write_text(
        "# comment\n"
        "EXPERIMENT_IMAGE=torch2pc-layerwise-thesis:0.1.0\n"
        "SOURCE_GIT_COMMIT='abc123'\n",
        encoding="utf-8",
    )
    values = runner.read_dotenv(path)
    assert values["EXPERIMENT_IMAGE"] == "torch2pc-layerwise-thesis:0.1.0"
    assert values["SOURCE_GIT_COMMIT"] == "abc123"


def test_verify_controlled_image_accepts_matching_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commit = "a" * 40
    image = "torch2pc-layerwise-thesis:test"
    (tmp_path / ".env").write_text(
        f"EXPERIMENT_IMAGE={image}\nSOURCE_GIT_COMMIT={commit}\n",
        encoding="utf-8",
    )

    def fake_output(args: list[str], *, cwd: Path) -> str:
        assert cwd == tmp_path
        if args == ["git", "rev-parse", "HEAD"]:
            return commit
        if args == ["git", "status", "--porcelain"]:
            return ""
        if args == ["docker", "image", "inspect", image]:
            return json.dumps(
                [{"Config": {"Labels": {"org.opencontainers.image.revision": commit}}}]
            )
        raise AssertionError(args)

    monkeypatch.setattr(runner, "output", fake_output)
    assert runner.verify_controlled_image(tmp_path) == (commit, image)


def test_verify_controlled_image_rejects_dirty_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commit = "b" * 40
    (tmp_path / ".env").write_text(
        f"EXPERIMENT_IMAGE=test\nSOURCE_GIT_COMMIT={commit}\n",
        encoding="utf-8",
    )

    def fake_output(args: list[str], *, cwd: Path) -> str:
        if args == ["git", "rev-parse", "HEAD"]:
            return commit
        if args == ["git", "status", "--porcelain"]:
            return " M src/file.py"
        raise AssertionError(args)

    monkeypatch.setattr(runner, "output", fake_output)
    with pytest.raises(RuntimeError, match="clean committed tree"):
        runner.verify_controlled_image(tmp_path)


def test_verify_controlled_image_rejects_stale_image(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commit = "c" * 40
    image = "test"
    (tmp_path / ".env").write_text(
        f"EXPERIMENT_IMAGE={image}\nSOURCE_GIT_COMMIT={commit}\n",
        encoding="utf-8",
    )

    def fake_output(args: list[str], *, cwd: Path) -> str:
        if args == ["git", "rev-parse", "HEAD"]:
            return commit
        if args == ["git", "status", "--porcelain"]:
            return ""
        if args == ["docker", "image", "inspect", image]:
            return json.dumps(
                [{"Config": {"Labels": {"org.opencontainers.image.revision": "d" * 40}}}]
            )
        raise AssertionError(args)

    monkeypatch.setattr(runner, "output", fake_output)
    with pytest.raises(RuntimeError, match="not built from the current commit"):
        runner.verify_controlled_image(tmp_path)
