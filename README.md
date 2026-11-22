# symlink-orphan-collector-kit

Finds and optionally removes symlinks whose targets no longer exist after a migration or cleanup.

```python
from symlink_orphan_collector_kit import find_orphaned_symlinks, remove_orphaned_symlinks

# List dangling links under a tree
orphans = find_orphaned_symlinks("/srv/app")
print(orphans)

# Remove them, getting back what succeeded and what failed
removed, failed = remove_orphaned_symlinks("/srv/app")
print("removed:", removed)
print("failed:", failed)
```

## Why this exists

After a migration, old symlinks often point at paths that were moved or deleted.  A plain
`find -L` follows links and can leave you removing the wrong thing, and `os.walk` by default
descends into symlinked directories.  This library walks a tree without following symlinks,
reports only the links whose targets are gone, and refuses to touch anything else.  The
trade-off is that it never follows a symlink, so a link to a directory is treated as a single
entry rather than a tree to scan.  That is the safe choice for a cleanup tool: you remove the
dangling link, not whatever it points at.

## The awkward edge

If the root you pass is itself a broken symlink, `find_orphaned_symlinks` returns an empty
list rather than the root itself.  A missing root has nothing to walk, and returning the root
would make the function's contract depend on its own argument in a surprising way.  If you
need to check a single path, use `os.path.islink` and `os.path.exists` directly.

## API

- `find_orphaned_symlinks(root)` -> `list[str]`
  Sorted paths of orphaned symlinks under `root`.  Returns `[]` if `root` does not exist.
- `remove_orphaned_symlinks(root)` -> `(list[str], list[str])`
  Removes orphaned symlinks and returns `(removed, failed)`, both sorted.
