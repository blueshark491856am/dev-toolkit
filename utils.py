"""Reusable helpers for the dev-toolkit project."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence


def find_project_root(
    start: str | os.PathLike[str] = ".",
    markers: Sequence[str] = (".git", "pyproject.toml", "setup.cfg"),
) -> Path:
    """Find the nearest parent directory containing a project marker.

    Args:
        start: File or directory from which to begin searching.
        markers: File or directory names that identify a project root.

    Returns:
        The resolved path of the nearest matching directory.

    Raises:
        ValueError: If no markers are supplied.
        FileNotFoundError: If no project root is found.
    """
    if not markers:
        raise ValueError("At least one project marker is required")

    current = Path(start).expanduser().resolve()
    if current.is_file():
        current = current.parent

    for directory in (current, *current.parents):
        if any((directory / marker).exists() for marker in markers):
            return directory

    raise FileNotFoundError(
        f"No project root containing {tuple(markers)!r} found from {current}"
    )


def run_command(
    command: Sequence[str],
    *,
    cwd: str | os.PathLike[str] | None = None,
    env: Mapping[str, str] | None = None,
    timeout: float | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a command without invoking a shell and capture its text output.

    Args:
        command: Executable and arguments to run.
        cwd: Optional working directory.
        env: Environment variables to merge with the current environment.
        timeout: Maximum execution time in seconds, or ``None`` for no limit.
        check: Raise an exception when the command exits unsuccessfully.

    Returns:
        The completed process, including its exit code, stdout, and stderr.

    Raises:
        ValueError: If the command is empty.
        subprocess.CalledProcessError: If ``check`` is true and the command fails.
        subprocess.TimeoutExpired: If the command exceeds ``timeout``.
    """
    if not command:
        raise ValueError("Command must not be empty")

    process_env = os.environ.copy()
    if env is not None:
        process_env.update(env)

    return subprocess.run(
        [os.fspath(argument) for argument in command],
        cwd=cwd,
        env=process_env,
        timeout=timeout,
        check=check,
        capture_output=True,
        text=True,
        shell=False,
    )


def load_json(path: str | os.PathLike[str], *, encoding: str = "utf-8") -> Any:
    """Load and decode a JSON document from disk.

    Args:
        path: Path to the JSON file.
        encoding: Text encoding used to read the file.

    Returns:
        The decoded JSON value.

    Raises:
        OSError: If the file cannot be read.
        json.JSONDecodeError: If the file does not contain valid JSON.
    """
    with Path(path).open("r", encoding=encoding) as file:
        return json.load(file)


def atomic_write_text(
    path: str | os.PathLike[str],
    content: str,
    *,
    encoding: str = "utf-8",
) -> Path:
    """Atomically replace a file with text content.

    A temporary file is written in the destination directory and then moved
    into place, preventing readers from observing a partially written file.

    Args:
        path: Destination file path.
        content: Text to write.
        encoding: Text encoding used for the output.

    Returns:
        The resolved destination path.

    Raises:
        OSError: If the directory cannot be created or the file cannot be written.
    """
    destination = Path(path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding=encoding,
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_file.write(content)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
            temporary_path = Path(temporary_file.name)

        os.replace(temporary_path, destination)
        temporary_path = None
        return destination
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)