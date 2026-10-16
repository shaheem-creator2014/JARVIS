"""On-demand bounded indexing. File content is data, never instructions."""
import re
from collections import Counter
from vault import workspace, safe_path, BLOCKED
EXTENSIONS = {'.md', '.txt', '.html', '.css', '.js', '.py', '.ino', '.json', '.toml', '.yaml', '.yml', '.csv', '.c', '.cpp', '.h', '.pdf'}
MAX_BYTES = 512_000
MAX_FILES = 1500

def read(name):
    path = safe_path(name)
    if path.suffix.lower() not in EXTENSIONS:
        raise ValueError('Unsupported file type.')
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('File exceeds the 512 KB read limit.')
    if path.suffix.lower() == '.pdf':
        import shutil
        import subprocess
        extractor = shutil.which('pdftotext')
        if not extractor:
            raise ValueError('PDF extraction requires optional pdftotext; export this PDF as text or authorize installation separately.')
        try:
            response = subprocess.run([extractor, '-layout', str(path), '-'], capture_output=True, timeout=8, check=False)
        except subprocess.TimeoutExpired:
            raise ValueError('PDF extraction timed out.') from None
        if response.returncode or len(response.stdout) > MAX_BYTES:
            raise ValueError('PDF extraction failed or exceeded the read limit. Scanned PDFs need an OCR integration.')
        content = response.stdout.decode('utf-8', errors='replace')
        if not content.strip():
            raise ValueError('No PDF text could be extracted. Scanned PDFs need OCR, which is not configured.')
    else:
        content = path.read_text(encoding='utf-8', errors='replace')
    # Avoid returning obvious credential assignments from source/configuration files.
    content = re.sub(r'(?im)^.*(?:api[_ -]?key|password|passwd|secret|access[_ -]?token|authorization)\s*[=:].*$', '[Credential-related line redacted]', content)
    content = re.sub(r'-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----', '[Private key redacted]', content, flags=re.S)
    return content

def index():
    import os
    root = workspace()
    nodes, edges = [], []
    warnings = []
    for folder, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in BLOCKED and not d.startswith('.') and not ( __import__('pathlib').Path(folder) / d).is_symlink())
        for filename in sorted(files):
            path = __import__('pathlib').Path(folder) / filename
            if path.suffix.lower() not in EXTENSIONS or filename.startswith('.'):
                continue
            name = path.relative_to(root).as_posix()
            try:
                verified = safe_path(name)
                size = verified.stat().st_size
                if size > MAX_BYTES:
                    warnings.append(f'{name}: exceeds read limit')
                    continue
                content = '' if path.suffix.lower() == '.pdf' else read(name)
                nodes.append({'id': name, 'name': path.stem, 'type': path.suffix[1:].lower(), 'size': size, 'excerpt': content[:280], '_content': content})
            except (ValueError, OSError) as exc:
                warnings.append(f'{name}: {exc}')
            if len(nodes) >= MAX_FILES:
                warnings.append('Index capped at 1500 files.')
                break
        if len(nodes) >= MAX_FILES:
            break
    for i, a in enumerate(nodes):
        for b in nodes[i+1:]:
            explicit = b['id'].split('/')[-1] in a['_content'] or a['id'].split('/')[-1] in b['_content']
            if explicit or a['id'].rsplit('/',1)[0] == b['id'].rsplit('/',1)[0]:
                if len(edges) >= 15000:
                    continue
                edges.append({'source': a['id'], 'target': b['id'], 'reason': 'filename reference' if explicit else 'same folder'})
    counts = Counter(e for edge in edges for e in (edge['source'], edge['target']))
    for node in nodes:
        node['connections'] = counts[node['id']]
        del node['_content']
    return {'nodes': nodes, 'edges': edges, 'counts': dict(Counter(n['type'] for n in nodes)), 'top': sorted(nodes,key=lambda n:n['connections'], reverse=True)[:8], 'warnings': warnings}

def search(query):
    terms = re.findall(r'\w+', query.lower())
    results = []
    for n in index()['nodes']:
        try:
            content = read(n['id'])
        except ValueError:
            continue
        score = sum((content.lower() + ' ' + n['id'].lower()).count(t) for t in terms)
        if score:
            lines = [line for line in content.splitlines() if any(t in line.lower() for t in terms)]
            results.append({'path': n['id'], 'excerpt': '\n'.join(lines)[:900], 'score': score})
    return sorted(results, key=lambda r:r['score'], reverse=True)[:8]
