"""Windows/VS Code entry point for the complete JARVIS application."""
import os
from pathlib import Path
import sys


def main():
    root = Path(__file__).resolve().parent
    if not (root / 'agent' / 'main.py').is_file():
        raise SystemExit('Extract the complete ZIP first. Keep agent/, ui/ and data/ beside jarvis.py.')
    config = root / '.env'
    if not config.exists():
        config.write_text((root / '.env.example').read_text(encoding='utf-8'), encoding='utf-8')
    sys.path.insert(0, str(root / 'agent'))
    import vault  # Loads the server-only .env before port selection.
    port = int(os.environ.get('JARVIS_PORT', '8720'))
    if not 1024 <= port <= 65535:
        raise SystemExit('JARVIS_PORT must be between 1024 and 65535.')
    import main as application
    try:
        # The server binds successfully before opening the browser.
        application.serve(open_browser=True)
    except OSError as exc:
        if exc.errno in (48, 98, 10048):
            raise SystemExit(f'Port {port} is already in use. Close your older JARVIS terminal, then try again.') from None
        raise


if __name__ == '__main__':
    main()
