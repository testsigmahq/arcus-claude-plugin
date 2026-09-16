"""Host-OS primitives — the one place a platform branch is allowed.

Every branch keys off a capability (does this import exist, does this call work)
rather than an OS or Python version, so there are no version checks to maintain.
Nothing here raises: it sits on the hook path, where a capture failure must never
surface in the user's session.

Import as ``hostos``; ``scripts/`` is on ``sys.path`` for hooks, CLIs and tests.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Iterator, Sequence
from contextlib import contextmanager

WINDOWS = os.name == "nt"

# POSIX advisory locks, Windows byte-range locks, or neither.
try:
    import fcntl as _fcntl
except ImportError:
    _fcntl = None
try:
    import msvcrt as _msvcrt
except ImportError:
    _msvcrt = None

LOCKING_AVAILABLE = _fcntl is not None or _msvcrt is not None

# Without this, every console app spawned from a hook flashes a window.
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0) if WINDOWS else 0


# --- Paths ------------------------------------------------------------------

# Reserved on every Windows release, with or without an extension.
_WIN_RESERVED = frozenset(
    {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"} | {f"COM{d}" for d in "123456789"} | {f"LPT{d}" for d in "123456789"}
)


def safe_component(name: str) -> str:
    """Make *name* legal as a path component on every OS.

    Applied everywhere, not just on Windows, so a session captured on macOS still
    unpacks on Windows.
    """
    if not name:
        return "part"
    if name.split(".", 1)[0].upper() in _WIN_RESERVED:
        name = "_" + name
    name = name.rstrip(". ")  # Windows drops these, colliding two distinct names
    return name or "part"


def long_path(path: str) -> str:
    """Return *path* uncapped by MAX_PATH. No-op off Windows.

    The prefix works on every Windows version, unlike the per-machine
    ``LongPathsEnabled`` flag, so we never have to ask which one this is.
    """
    if not WINDOWS or not path or path.startswith("\\\\?\\"):
        return path
    try:
        abs_path = os.path.abspath(path)
    except (OSError, ValueError):
        return path
    if abs_path.startswith("\\\\"):  # \\server\share -> \\?\UNC\server\share
        return "\\\\?\\UNC" + abs_path[1:]
    return "\\\\?\\" + abs_path


def makedirs(path: str) -> bool:
    """MAX_PATH-proof ``os.makedirs(exist_ok=True)``. False on failure."""
    if not path:
        return True
    try:
        os.makedirs(long_path(path), exist_ok=True)
        return True
    except OSError:
        return False


# --- Locking ----------------------------------------------------------------


def _acquire(fd: int) -> bool:
    if _fcntl is not None:
        try:
            _fcntl.flock(fd, _fcntl.LOCK_EX)
            return True
        except OSError:
            return False
    if _msvcrt is not None:
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            # LK_LOCK retries ~10s then raises; a lost race degrades to unlocked.
            _msvcrt.locking(fd, _msvcrt.LK_LOCK, 1)
            return True
        except OSError:
            return False
    return False


def _release(fd: int) -> None:
    try:
        if _fcntl is not None:
            _fcntl.flock(fd, _fcntl.LOCK_UN)
        elif _msvcrt is not None:
            os.lseek(fd, 0, os.SEEK_SET)
            _msvcrt.locking(fd, _msvcrt.LK_UNLCK, 1)
    except OSError:
        pass


@contextmanager
def file_lock(path: str) -> Iterator[bool]:
    """Exclusive cross-process lock for *path*; yields whether it was taken.

    Locks a sidecar ``<path>.lock``, never the file itself: Windows byte-range
    locks are mandatory, so locking the data file would block readers and collide
    with ``truncate()``.
    """
    lock_path = str(path) + ".lock"
    parent = os.path.dirname(lock_path)
    if parent and not makedirs(parent):
        yield False
        return
    try:
        fd = os.open(long_path(lock_path), os.O_RDWR | os.O_CREAT, 0o600)
    except OSError:
        yield False
        return
    locked = False
    try:
        locked = _acquire(fd)
        yield locked
    finally:
        if locked:
            _release(fd)
        try:
            os.close(fd)
        except OSError:
            pass


# --- Permissions ------------------------------------------------------------


def restrict_file(path: str) -> None:
    """Make *path* owner-only on any OS.

    ``chmod`` is the whole story on POSIX; on Windows it only flips the read-only
    bit, leaving the file readable by every account, so the ACL is set explicitly.
    """
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    if not WINDOWS:
        return
    user = os.environ.get("USERNAME")
    if not user:
        return
    # Domain-qualified: a local and a domain account can share a bare name.
    domain = os.environ.get("USERDOMAIN")
    principal = f"{domain}\\{user}" if domain else user
    run_text(["icacls", path, "/inheritance:r", "/grant:r", f"{principal}:F"], timeout=10)


# --- Subprocess -------------------------------------------------------------


def run_text(cmd: Sequence[str], cwd: str | None = None, timeout: float = 5) -> str | None:
    """Run *cmd*, returning stripped stdout or None on any failure.

    Decodes UTF-8 explicitly — ``text=True`` uses the Windows console codepage and
    raises on a non-ASCII branch name. Resolves via PATHEXT so ``.cmd`` shims
    (gh installed by npm or scoop) are found.
    """
    if not cmd:
        return None
    work_dir = (cwd or "").strip() or None
    if work_dir and not os.path.isdir(work_dir):
        work_dir = None
    argv = list(cmd)
    resolved = shutil.which(argv[0], path=os.environ.get("PATH"))
    if resolved:
        argv[0] = resolved
    try:
        result = subprocess.run(
            argv,
            capture_output=True,
            cwd=work_dir,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
            creationflags=_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    if result.returncode != 0:
        return None
    return (result.stdout or "").strip() or None
