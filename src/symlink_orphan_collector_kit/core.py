import os
from typing import Iterator, List, Tuple


def _is_orphaned(path: str) -> bool:
    """Return True if *path* is a symlink whose target does not exist.

    ``os.path.islink`` is used rather than ``os.path.isdir``/``os.path.isfile``
    because those follow the link and return False for a broken link, which is
    exactly the case we want to detect.  ``os.path.lexists`` would also work but
    is less explicit about the intent.
    """
    return os.path.islink(path) and not os.path.exists(path)


def find_orphaned_symlinks(root: str) -> List[str]:
    """Walk *root* and return a sorted list of paths to orphaned symlinks.

    The walk is top-down and does not follow symlinks, so a symlink to a
    directory is never descended into.  Only the symlink itself is considered;
    its target is never traversed.  This matches the usual expectation for a
    cleanup tool: you want to remove the dangling link, not whatever it points
    at (which may be outside the tree).

    ``root`` may itself be a symlink.  If it is orphaned it is returned; if it
    is valid the walk starts at its target, because ``os.walk`` follows the
    top-level path it is given.  That is the least surprising behaviour for a
    user who passes a symlinked directory.
    """
    if not os.path.exists(root):
        # A non-existent root is not an error; there is simply nothing to find.
        return []

    found: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        # Check the directory entries that are symlinks.  os.walk yields them in
        # dirnames when they point to directories, and in filenames otherwise,
        # so both lists must be inspected.
        for name in dirnames + filenames:
            path = os.path.join(dirpath, name)
            if _is_orphaned(path):
                found.append(path)

        # Do not recurse into symlinked directories.  os.walk with
        # followlinks=False already avoids this, but pruning dirnames makes the
        # intent explicit and guards against platform differences.
        dirnames[:] = [d for d in dirnames if not os.path.islink(os.path.join(dirpath, d))]

    # Sort for deterministic output.  Callers often feed the result to a
    # removal step, and stable ordering makes logs and tests reproducible.
    found.sort()
    return found


def remove_orphaned_symlinks(root: str) -> Tuple[List[str], List[str]]:
    """Remove orphaned symlinks under *root*.

    Returns a pair ``(removed, failed)`` where ``removed`` is the sorted list of
    paths that were unlinked and ``failed`` is the sorted list of paths that
    could not be removed (for example because of permissions).  The caller can
    decide whether a partial failure is acceptable.

    Only ``os.unlink`` is used.  ``os.remove`` is an alias on most platforms but
    ``unlink`` is the POSIX name and works on Windows as well for files and
    symlinks.
    """
    removed: List[str] = []
    failed: List[str] = []
    for path in find_orphaned_symlinks(root):
        try:
            os.unlink(path)
            removed.append(path)
        except OSError:
            failed.append(path)
    return removed, failed
