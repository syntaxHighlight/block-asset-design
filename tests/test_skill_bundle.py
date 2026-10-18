"""A copied collection must work without sibling skills or the source checkout."""
from pathlib import Path
import re
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / 'skills/block-asset-design'


class SkillBundleTests(unittest.TestCase):
    def test_collection_references_stay_inside_isolated_install(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            installed = Path(directory).resolve() / 'block-asset-design'
            shutil.copytree(BUNDLE, installed, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            entry = installed / 'SKILL.md'
            self.assertTrue(entry.is_file())
            for document in installed.rglob('*.md'):
                for target in re.findall(r'\]\(([^)]+)\)', document.read_text(encoding='utf-8')):
                    if target.startswith(('https://', 'http://', '#')):
                        continue
                    resolved = (document.parent / target.split('#', 1)[0]).resolve()
                    with self.subTest(document=document.relative_to(installed), target=target):
                        self.assertTrue(resolved.is_relative_to(installed))
                        self.assertTrue(resolved.is_file(), str(resolved))

    def test_nested_skills_have_unique_discoverable_names(self) -> None:
        names: set[str] = set()
        for document in BUNDLE.rglob('SKILL.md'):
            content = document.read_text(encoding='utf-8')
            match = re.search(r'^name: ([a-z0-9-]+)$', content, re.MULTILINE)
            self.assertIsNotNone(match, str(document))
            if match is None:
                continue
            name = match.group(1)
            self.assertNotIn(name, names)
            names.add(name)
        self.assertIn('block-asset-design', names)
        self.assertIn('game-acceptance', names)


if __name__ == '__main__':
    unittest.main()
