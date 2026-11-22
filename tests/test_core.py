import os
import tempfile
import unittest

from symlink_orphan_collector_kit import find_orphaned_symlinks, remove_orphaned_symlinks


class TestFindOrphanedSymlinks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def _make_file(self, relpath: str) -> str:
        path = os.path.join(self.root, relpath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write("x")
        return path

    def _make_symlink(self, relpath: str, target: str) -> str:
        path = os.path.join(self.root, relpath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        os.symlink(target, path)
        return path

    def test_empty_directory(self):
        self.assertEqual(find_orphaned_symlinks(self.root), [])

    def test_missing_root_returns_empty(self):
        self.assertEqual(find_orphaned_symlinks(os.path.join(self.root, "nope")), [])

    def test_valid_symlink_is_not_orphaned(self):
        self._make_file("target.txt")
        self._make_symlink("link.txt", "target.txt")
        self.assertEqual(find_orphaned_symlinks(self.root), [])

    def test_orphaned_symlink_is_found(self):
        link = self._make_symlink("link.txt", "missing.txt")
        self.assertEqual(find_orphaned_symlinks(self.root), [link])

    def test_symlink_to_directory_is_not_descended(self):
        # A symlink to a directory should be reported only if the directory is
        # missing, and the walk must not enter it.
        self._make_file("real_dir/file.txt")
        self._make_symlink("dirlink", "real_dir")
        self.assertEqual(find_orphaned_symlinks(self.root), [])

    def test_orphaned_symlink_to_directory_is_found(self):
        link = self._make_symlink("dirlink", "missing_dir")
        self.assertEqual(find_orphaned_symlinks(self.root), [link])

    def test_nested_orphans_are_sorted(self):
        a = self._make_symlink("a/link", "missing")
        b = self._make_symlink("b/link", "missing")
        self.assertEqual(find_orphaned_symlinks(self.root), sorted([a, b]))

    def test_root_itself_is_orphaned_symlink(self):
        # os.walk on a broken symlink root yields nothing, so the function
        # returns an empty list.  This is the documented behaviour: a missing
        # root has nothing to find.
        link = os.path.join(self.tmp.name, "rootlink")
        os.symlink("missing", link)
        self.assertEqual(find_orphaned_symlinks(link), [])


class TestRemoveOrphanedSymlinks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def _make_symlink(self, relpath: str, target: str) -> str:
        path = os.path.join(self.root, relpath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        os.symlink(target, path)
        return path

    def test_removes_orphans(self):
        link = self._make_symlink("link", "missing")
        removed, failed = remove_orphaned_symlinks(self.root)
        self.assertEqual(removed, [link])
        self.assertEqual(failed, [])
        self.assertFalse(os.path.lexists(link))

    def test_keeps_valid_symlinks(self):
        target = os.path.join(self.root, "target")
        with open(target, "w") as fh:
            fh.write("x")
        link = self._make_symlink("link", "target")
        removed, failed = remove_orphaned_symlinks(self.root)
        self.assertEqual(removed, [])
        self.assertEqual(failed, [])
        self.assertTrue(os.path.lexists(link))

    def test_no_orphans_returns_empty_lists(self):
        removed, failed = remove_orphaned_symlinks(self.root)
        self.assertEqual(removed, [])
        self.assertEqual(failed, [])


if __name__ == "__main__":
    unittest.main()
