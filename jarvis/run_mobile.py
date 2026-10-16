"""Android/portable Python launcher; needs the complete jarvis folder beside it."""
import argparse
import os
from pathlib import Path
import runpy
import sys


def main():
    parser = argparse.ArgumentParser(description="Run JARVIS with the mobile interface on this device.")
    parser.add_argument('--port', type=int, default=8720)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error('Choose a port from 1024 to 65535.')
    root = Path(__file__).resolve().parent
    if not (root / 'agent' / 'main.py').is_file():
        parser.error('Extract the complete JARVIS mobile package; this launcher needs agent/ and ui/.')
    os.environ['JARVIS_UI_MODE'] = 'mobile'
    os.environ['JARVIS_PORT'] = str(args.port)
    sys.path.insert(0, str(root / 'agent'))
    print(f'On this same phone, open http://127.0.0.1:{args.port}/?device=mobile', flush=True)
    print('Keep Python running. Mobile mode does not enable real files, paid APIs or computer control.', flush=True)
    runpy.run_path(str(root / 'agent' / 'main.py'), run_name='__main__')


if __name__ == '__main__':
    main()
