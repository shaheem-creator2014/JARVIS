"""Discover launchable apps; no shell, arbitrary commands or destructive actions."""
import os
import platform
import shutil
import subprocess
import shlex
import configparser
from pathlib import Path
from urllib.parse import urlparse
from vault import ROOT, safe_path

def discover():
    system = platform.system()
    apps = {}
    if system == 'Linux':
        for root in [Path('/usr/share/applications'), Path('/usr/local/share/applications'), Path.home()/'.local/share/applications']:
            if not root.exists():
                continue
            for p in root.glob('*.desktop'):
                try:
                    cfg = configparser.ConfigParser(interpolation=None, strict=False)
                    cfg.read(p)
                    entry = cfg['Desktop Entry']
                    if entry.get('Type') != 'Application' or entry.get('Hidden') == 'true' or entry.get('NoDisplay') == 'true':
                        continue
                    args = [a for a in shlex.split(entry.get('Exec','')) if not a.startswith('%')]
                    if args and shutil.which(args[0]) and not any('%' in a for a in args):
                        apps[entry.get('Name',p.stem)] = args
                except (OSError, KeyError, ValueError, configparser.Error):
                    continue
    elif system == 'Darwin':
        for root in [Path('/Applications'), Path.home()/'Applications', Path('/System/Applications')]:
            if root.exists():
                for p in root.glob('*.app'):
                    apps[p.stem] = ['open','-a',str(p)]
    elif system == 'Windows':
        for root in [Path(os.environ.get('PROGRAMDATA','C:/ProgramData'))/'Microsoft/Windows/Start Menu/Programs', Path(os.environ.get('APPDATA',''))/'Microsoft/Windows/Start Menu/Programs']:
            if root.exists():
                for p in root.rglob('*.lnk'):
                    apps[p.stem] = [str(p)]
    shortcuts = ROOT / '.local' / 'applications.json'
    if shortcuts.exists():
        import json
        for name, args in json.loads(shortcuts.read_text()).items():
            if isinstance(args,list) and args and all(isinstance(a,str) for a in args):
                apps[name] = args
    return apps

def control(kind, target):
    if os.environ.get('JARVIS_DEMO','1') == '1':
        raise ValueError('Computer actions are disabled in demo mode. No action was attempted.')
    if os.environ.get('JARVIS_ENABLE_COMPUTER','0') != '1':
        raise ValueError('Enable JARVIS_ENABLE_COMPUTER explicitly on your laptop to allow launches.')
    system = platform.system()
    if kind == 'check_python':
        path = safe_path(target)
        if path.suffix != '.py' or not path.is_file() or path.stat().st_size > 512000:
            raise ValueError('Select an existing Python source file below 512 KB.')
        try:
            compile(path.read_text(encoding='utf-8'), target, 'exec')
        except SyntaxError as exc:
            raise ValueError(f'Python syntax error on line {exc.lineno}: {exc.msg}') from None
        return {'status':'passed','target':target,'verified':True,'detail':'Python syntax check passed. No project code was executed or changed.'}
    if kind == 'app':
        apps = discover()
        matches = [k for k in apps if k.casefold() == target.casefold()]
        if not matches:
            matches = [k for k in apps if target.casefold() in k.casefold()]
        if len(matches) != 1:
            raise ValueError('Application not found or ambiguous. Select an exact discovered application name.')
        args = apps[matches[0]]
    elif kind in ('file','folder'):
        path = safe_path(target)
        if not path.exists():
            raise ValueError('File or folder does not exist.')
        args = ['open',str(path)] if system == 'Darwin' else ['xdg-open',str(path)]
        if system == 'Windows':
            os.startfile(str(path))
            return {'status':'requested', 'target':target, 'verified':False, 'detail':'Windows accepted the launch request; opening cannot be verified.'}
    elif kind == 'website':
        parsed = urlparse(target)
        if parsed.scheme not in ('https','http') or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError('Use a public HTTP(S) URL without credentials.')
        args = ['open',target] if system == 'Darwin' else ['xdg-open',target]
        if system == 'Windows':
            os.startfile(target)
            return {'status':'requested','target':target,'verified':False,'detail':'Browser launch requested; page loading cannot be verified.'}
    else:
        raise ValueError('Allowed actions: app, file, folder, website, check_python. Shell commands and deletion are not supported.')
    try:
        p = subprocess.Popen(args, shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            _, err = p.communicate(timeout=2)
            if p.returncode:
                raise ValueError('Launcher failed: ' + err.decode(errors='replace')[:300])
            status = 'launcher completed'
        except subprocess.TimeoutExpired:
            status = 'process started'
    except OSError as exc:
        raise ValueError(f'Unable to launch: {exc}') from exc
    return {'status':status,'target':target,'verified':False,'detail':'Launch attempted. Application UI or page completion cannot be verified by this integration.'}
