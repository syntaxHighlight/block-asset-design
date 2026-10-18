#!/usr/bin/env python3
"""Build the standalone release tools and their SHA-256 checksum (stdlib only)."""
import argparse
import gzip
import hashlib
from pathlib import Path
import tarfile


ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'checks': ROOT / 'skills/block-asset-design/shared/scripts',
    'texture': ROOT / 'skills/block-asset-design/texture/scripts',
    'review': ROOT / 'skills/block-asset-design/review/scripts',
    'resources': ROOT / 'skills/block-asset-design/mod-resource-extract/scripts',
}


def package_files() -> list[tuple[Path, str]]:
    """Map source files to tool paths without including the skill installation layout."""
    files: dict[str, Path] = {}
    for destination, source in SOURCES.items():
        for path in sorted(source.rglob('*')):
            relative = path.relative_to(source)
            if any(part.startswith('.') or part == '__pycache__' for part in relative.parts):
                continue
            if path.suffix in ('.pyc', '.pyo'):
                continue
            if path.is_symlink():
                raise ValueError(f'symlink is not a distributable tool file: {path}')
            if path.is_file():
                files[f'{destination}/{relative.as_posix()}'] = path
        # Dependencies and any applicable notices accompany each tool family.
        for directory in (source.parent, source.parent.parent):
            if directory == ROOT / 'skills':
                continue
            for path in sorted(directory.iterdir()):
                if path.is_file() and (
                    path.name == 'requirements.txt'
                    or path.name.upper().startswith(('LICENSE', 'COPYING', 'NOTICE'))
                ):
                    target = f'{destination}/{path.name}'
                    if target in files and files[target] != path:
                        raise ValueError(f'conflicting package path: {target}')
                    files[target] = path
    for path in sorted(ROOT.iterdir()):
        if path.is_file() and path.name.upper().startswith(('LICENSE', 'COPYING', 'NOTICE')):
            files[path.name] = path
    return [(path, name) for name, path in sorted(files.items())]


def build_package(output: Path) -> Path:
    """Write a reproducible archive and a checksum usable by sha256sum/shasum."""
    if not output.name.endswith('.tar.gz'):
        raise ValueError('output filename must end with .tar.gz')
    files = package_files()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('wb') as raw:
        with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode='w') as archive:
                for path, name in files:
                    info = tarfile.TarInfo(name)
                    info.size = path.stat().st_size
                    info.mode = 0o644
                    with path.open('rb') as source:
                        archive.addfile(info, source)
    checksum = output.with_name(output.name + '.sha256')
    checksum.write_text(f'{hashlib.sha256(output.read_bytes()).hexdigest()}  {output.name}\n', encoding='utf-8')
    return checksum


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True,
                        help='archive path, e.g. /tmp/block-asset-design-scripts.tar.gz')
    args = parser.parse_args()
    try:
        checksum = build_package(args.output)
    except ValueError as error:
        parser.error(str(error))
    print(args.output)
    print(checksum)


if __name__ == '__main__':
    main()
