#!/usr/bin/env python3
"""Copy tools from the installed skill into a new project tools directory."""
import argparse
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[2]
SOURCES = {
    'checks': ROOT / 'shared/scripts',
    'texture': ROOT / 'texture/scripts',
    'review': ROOT / 'review/scripts',
    'resources': ROOT / 'mod-resource-extract/scripts',
}


def tool_files() -> list[tuple[Path, str]]:
    """Keep tool dependencies and notices without the skill directory layout."""
    files: dict[str, Path] = {}

    def add_file(path: Path, target: str) -> None:
        if path.is_symlink():
            raise ValueError(f'symlink is not a tool file: {path}')
        if target in files and files[target] != path:
            raise ValueError(f'conflicting tool path: {target}')
        files[target] = path

    for destination, source in SOURCES.items():
        if not source.is_dir() or source.is_symlink():
            raise ValueError(f'missing or invalid tool source: {source}')
        for path in sorted(source.rglob('*')):
            relative = path.relative_to(source)
            if any(part.startswith('.') or part == '__pycache__' for part in relative.parts):
                continue
            if path.suffix in ('.pyc', '.pyo'):
                continue
            if path.is_symlink():
                raise ValueError(f'symlink is not a tool file: {path}')
            if path.is_file():
                add_file(path, f'{destination}/{relative.as_posix()}')
        for directory in (source.parent, ROOT):
            for path in sorted(directory.iterdir()):
                if path.is_file() and (
                    path.name == 'requirements.txt'
                    or path.name.upper().startswith(('LICENSE', 'COPYING', 'NOTICE'))
                ):
                    add_file(path, f'{destination}/{path.name}')
    for path in sorted(ROOT.iterdir()):
        if path.is_file() and path.name.upper().startswith(('LICENSE', 'COPYING', 'NOTICE')):
            add_file(path, path.name)
    return [(path, name) for name, path in sorted(files.items())]


def copy_tools(output: Path) -> None:
    """Create a first copy; existing project files require a separate merge."""
    if output.exists() or output.is_symlink():
        raise ValueError(f'output already exists; compare and merge separately: {output}')
    files = tool_files()
    output.mkdir(parents=True)
    try:
        for source, relative in files:
            target = output / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    except OSError:
        shutil.rmtree(output)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True,
                        help='new project tools directory, e.g. tools/block-asset-design')
    args = parser.parse_args()
    try:
        copy_tools(args.output)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(args.output)


if __name__ == '__main__':
    main()
