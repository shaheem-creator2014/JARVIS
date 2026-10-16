"""Dated, atomic Markdown memories. No silent writes."""
import re
import uuid
from datetime import datetime
from vault import ROOT
DIRECTORY = ROOT / 'memory'
SENSITIVE = re.compile(r'(password|passwd|api[ _-]?key|secret|token|bearer|private[ _-]?key|sk-[A-Za-z0-9]|xi-api-key)', re.I)

def listing():
    DIRECTORY.mkdir(exist_ok=True)
    return [{'id': p.name, 'text': p.read_text(encoding='utf-8')} for p in sorted(DIRECTORY.glob('*.md')) if not p.is_symlink()]

def target(name):
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}-[a-f0-9]{12}\.md', name):
        raise ValueError('Select an actual memory ID.')
    p = DIRECTORY / name
    if p.is_symlink():
        raise ValueError('Symlink memories are not allowed.')
    return p

def remember(text, identifier=None):
    text = text.strip()
    if not text or len(text) > 4000:
        raise ValueError('Memory must contain 1–4000 characters.')
    if SENSITIVE.search(text):
        raise ValueError('Secrets and credential-related information cannot be saved in memory.')
    DIRECTORY.mkdir(exist_ok=True)
    name = identifier or f'{datetime.now().date().isoformat()}-{uuid.uuid4().hex[:12]}.md'
    path = target(name)
    if identifier and not path.exists():
        raise ValueError('Memory not found.')
    temporary = path.with_suffix('.tmp')
    temporary.write_text(text + '\n', encoding='utf-8')
    temporary.replace(path)
    return {'id': name, 'text': text, 'operation': 'updated' if identifier else 'saved'}

def forget(identifier):
    path = target(identifier)
    path.unlink()
    return {'id': identifier, 'operation': 'deleted', 'verified': not path.exists()}
