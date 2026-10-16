"""Build a credential-free source ZIP and an offline Python installer."""
import argparse
import base64
import hashlib
import io
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
FILES = ('jarvis.py', 'run_mobile.py', 'START-JARVIS.bat', 'START-HERE.txt',
         'README.md', 'CLAUDE.md', '.gitignore', '.env.example', 'package_release.py')


def build(output):
    output.mkdir(parents=True, exist_ok=True)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for folder in ('agent', 'ui', 'tests'):
            for path in sorted((ROOT / folder).glob('*')):
                if path.is_file() and path.suffix in ('.py', '.md', '.html', '.css', '.js'):
                    if path.is_symlink():
                        raise ValueError('Release files must not be symlinks.')
                    archive.write(path, 'JARVIS/' + path.relative_to(ROOT).as_posix())
        archive.write(ROOT / 'data' / 'generator.py', 'JARVIS/data/generator.py')
        for name in FILES:
            path = ROOT / name
            if path.is_symlink():
                raise ValueError('Release files must not be symlinks.')
            data = path.read_bytes()
            if name.endswith('.bat'):
                data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            archive.writestr('JARVIS/' + name, data)
        # Never read the real .env, personal memories, demo outputs or backups.
        archive.writestr('JARVIS/.env', (ROOT / '.env.example').read_bytes())
        archive.writestr('JARVIS/memory/', b'')
    raw = buffer.getvalue()
    digest = hashlib.sha256(raw).hexdigest()
    target = output / 'JARVIS-Windows.zip'
    target.write_bytes(raw)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        assert archive.testzip() is None
        assert all(name.startswith('JARVIS/') for name in archive.namelist())
        assert not any('/.local/' in name or '__pycache__' in name for name in archive.namelist())
    encoded = base64.b64encode(raw).decode('ascii')
    chunks = '\n'.join(encoded[i:i+100] for i in range(0, len(encoded), 100))
    installer = '''"""Offline JARVIS setup: extracts only bundled source, installs no packages.
Run: py -3 JARVIS-Setup.py
"""
import base64
import hashlib
import io
from pathlib import Path, PurePosixPath
import zipfile

ARCHIVE = """__PAYLOAD__"""
SHA256 = '__DIGEST__'


def main():
    parent = Path(__file__).resolve().parent
    destination = parent / 'JARVIS'
    if destination.exists():
        raise SystemExit('A JARVIS folder already exists here. Move this setup file to a new folder, then run again. Existing files were not changed.')
    raw = base64.b64decode(ARCHIVE)
    if hashlib.sha256(raw).hexdigest() != SHA256:
        raise SystemExit('Setup contents are damaged. No files were extracted.')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if archive.testzip() is not None:
            raise SystemExit('Archive verification failed.')
        for item in archive.infolist():
            parts = PurePosixPath(item.filename).parts
            if (not parts or parts[0] != 'JARVIS' or '..' in parts
                or '\\\\' in item.filename or PurePosixPath(item.filename).is_absolute()
                or any(':' in part for part in parts)
                or item.external_attr >> 16 & 0o170000 == 0o120000):
                raise SystemExit('Unsafe archive member. Nothing was extracted.')
        archive.extractall(parent)
    print('JARVIS created:', destination)
    print('Next: double-click START-JARVIS.bat in that folder.')
    print('Or open the folder in VS Code and run: py -3 jarvis.py')
    print('No packages were installed, and no API requests were made.')


if __name__ == '__main__':
    main()
'''.replace('__PAYLOAD__', chunks).replace('__DIGEST__', digest)
    (output / 'JARVIS-Setup.py').write_text(installer, encoding='utf-8')
    (output / 'SHA256.txt').write_text(digest + '  JARVIS-Windows.zip\n', encoding='ascii')
    print(f'ZIP: {target} ({len(raw):,} bytes)')
    print('Offline installer:', output / 'JARVIS-Setup.py')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / '.local' / 'release')
    build(parser.parse_args().output)
