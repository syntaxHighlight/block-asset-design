"""Keep the restricted IE catalog distributable without its source artwork."""
import hashlib
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / 'skills/block-asset-design/references/material-library'
IE = LIBRARY / 'ie-textures'


class MaterialLibraryTests(unittest.TestCase):
    def test_metadata_only_distribution(self) -> None:
        # Adding any payload requires an explicit review of redistribution rights.
        expected = {
            f'ie-textures/{name}' for name in
            ('INDEX.md', 'NOTICE.md', 'catalog.json', 'LICENSE.IE.txt', 'provenance.json')
        }
        paths = list(LIBRARY.rglob('*'))
        self.assertFalse(any(path.is_symlink() for path in paths))
        self.assertEqual(
            {path.relative_to(LIBRARY).as_posix() for path in paths if path.is_file()},
            expected,
        )
        for name in expected:
            (LIBRARY / name).read_text(encoding='utf-8')

    def test_fixed_source_metadata_is_preserved(self) -> None:
        expected = {
            'catalog.json': '928a635820279bfd3ff08d093c9235bd627faff3194eae0b7f32825a5f0c7777',
            'LICENSE.IE.txt': '1cfd83b717bae58527751de2d494e8d0f4c8c8124049dbc521ee66569bd4a5a1',
        }
        for name, digest in expected.items():
            with self.subTest(name=name):
                self.assertEqual(hashlib.sha256((IE / name).read_bytes()).hexdigest(), digest)

    def test_material_navigation_resolves_within_installed_skills(self) -> None:
        skills = ROOT / 'skills'
        documents = [
            skills / 'block-asset-design/references/material-sources.md',
            skills / 'block-asset-design/shared/references/resources.md',
            skills / 'block-asset-design/shared/references/material-permissions.md',
            skills / 'block-asset-design/shared/references/profiles/ie-style.md',
            skills / 'block-asset-design/mod-resource-extract/SKILL.md',
            skills / 'block-asset-design/mod-resource-extract/references/manifest.md',
            *IE.glob('*.md'),
        ]
        for document in documents:
            content = document.read_text(encoding='utf-8')
            self.assertNotIn('<img', content)
            for target in re.findall(r'\]\(([^)]+)\)', content):
                if target.startswith(('https://', 'http://', '#')):
                    continue
                resolved = (document.parent / target.split('#', 1)[0]).resolve()
                with self.subTest(document=document.name, target=target):
                    self.assertTrue(resolved.is_relative_to(skills))
                    self.assertTrue(resolved.is_file(), str(resolved))


if __name__ == '__main__':
    unittest.main()
