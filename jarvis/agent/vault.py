"""Configuration and confined filesystem access. Never expose credentials."""
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def load_env():
    path = ROOT / '.env'
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip() and not line.lstrip().startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip().strip('\"\''))
load_env()

def workspace():
    if os.environ.get('JARVIS_DEMO', '1') == '1':
        return ROOT / 'data' / 'demo'
    value = os.environ.get('JARVIS_WORKSPACE', '')
    if not value:
        raise ValueError('Set JARVIS_WORKSPACE to the actual Jarvis AI folder before enabling real mode.')
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise ValueError('Configured workspace is not an existing directory.')
    return root

BLOCKED = {'.env', '.git', 'node_modules', '.ssh', '.aws', '__pycache__', 'memory'}

def safe_path(name, root=None):
    root = (root or workspace()).resolve()
    relative = Path(name)
    if relative.is_absolute() or any(p in BLOCKED or p.startswith('.env') for p in relative.parts):
        raise ValueError('This path is not authorized.')
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or path == root:
        raise ValueError('Path must stay inside the configured workspace.')
    if any(p in BLOCKED or p.startswith('.env') for p in path.relative_to(root).parts):
        raise ValueError('Sensitive paths are excluded.')
    return path
