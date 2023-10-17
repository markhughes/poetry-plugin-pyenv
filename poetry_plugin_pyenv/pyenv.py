from __future__ import annotations
import os
import platform

import re
import subprocess

from typing import TYPE_CHECKING

from poetry.core.constraints.version import Version


if TYPE_CHECKING:
    from re import Match
    from re import Pattern
    from subprocess import CompletedProcess
    from typing import Iterator


# See: https://regex101.com/r/Bz2g17/1
PYTHON_VERSION_REGEX: Pattern[str] = re.compile(
    r"^\s*(\d+\S*)\s*$", re.IGNORECASE | re.MULTILINE
)


def is_installed(version: Version) -> bool:
    result: CompletedProcess[bytes] = subprocess.run(
        [find_pyenv(), "versions", "--bare"], capture_output=True
    )
    return (
        result.returncode == 0
        and re.search(version.text.split('-')[0], result.stdout.decode("utf-8"), flags=re.MULTILINE)
        is not None
    )


def install(version: Version) -> None:
    subprocess.run([find_pyenv(), "install", version.text], check=True)


def ensure_installed(version: Version) -> None:
    if not is_installed(version):
        install(version)


def get_local_version() -> Version | None:
    result: CompletedProcess[bytes] = subprocess.run(
        [find_pyenv(), "local"], capture_output=True
    )
    if result.returncode != 0 or re.search(r"no local version", result.stdout.decode("utf-8")):
        return None
    return Version.parse(result.stdout.decode("utf-8").split('-')[0])


def set_local_version(version: Version) -> None:
    subprocess.run([find_pyenv(), "local", version.text])


def get_remote_versions() -> list[Version]:
    result: CompletedProcess[bytes] = subprocess.run(
        [find_pyenv(), "install", "--list"], check=True, capture_output=True
    )
    output: str = result.stdout.decode("utf-8")
    matched_versions: Iterator[Match[str]] = re.finditer(PYTHON_VERSION_REGEX, output)
    return [Version.parse(v.group(1).split('-')[0]) for v in matched_versions]


_pyenv_cache = None
_was_located = None

def find_pyenv():
    global _pyenv_cache, _was_located

    if _pyenv_cache:
        return _pyenv_cache

    _was_located = True 

    try:
        if platform.system() == 'Windows':
            _pyenv_cache = subprocess.check_output(['where', 'pyenv'], text=True).strip().splitlines()[0]
        else:
            _pyenv_cache = subprocess.check_output(['which', 'pyenv'], text=True).strip()
        return _pyenv_cache
    except subprocess.CalledProcessError:
        pass

    if platform.system() == 'Windows':
        common_dirs = [
            os.path.join(os.environ['USERPROFILE'], '.pyenv', 'pyenv-win', 'bin'),
            os.path.join(os.environ['USERPROFILE'], '.pyenv', 'bin'),
            'C:\\.pyenv\\pyenv-win\\bin',
            'C:\\.pyenv\\bin'
        ]

        for dir in common_dirs:
            if os.path.exists(os.path.join(dir, 'pyenv.exe')) or os.path.exists(os.path.join(dir, 'pyenv.bat')):
                _pyenv_cache = os.path.join(dir, 'pyenv.exe') if os.path.exists(os.path.join(dir, 'pyenv.exe')) else os.path.join(dir, 'pyenv.bat')
                return _pyenv_cache

    else:
        try:
            if subprocess.check_output(['bash', '-c', 'type -t pyenv'], text=True).strip() == 'function':
                _pyenv_cache = 'pyenv (shell function)'
                return _pyenv_cache
        except subprocess.CalledProcessError:
            pass

    _pyenv_cache = "pyenv"
    _was_located = False

    return _pyenv_cache

def was_located():
    global _was_located
    return _was_located