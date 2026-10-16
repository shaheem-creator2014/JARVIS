"""Modular tool functions: each returns spoken text and a structured card."""
import json
import os
import re
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
import data
import memory
import computer
from vault import ROOT

def result(spoken, title, details, kind='info'):
    return {'spoken':spoken,'card':{'title':title,'kind':kind,'details':details}}

def search_brain(query):
    found = data.search(query)
    return result(f'Found {len(found)} matching files.' if found else 'No matching files were found.', 'Workspace search', found)

def read_files(paths):
    if not isinstance(paths,list) or not 1 <= len(paths) <= 8:
        raise ValueError('Select one to eight file paths.')
    files = [{'path':p,'content':data.read(p)[:16000]} for p in paths if isinstance(p,str)]
    if len(files) != len(paths):
        raise ValueError('All paths must be strings.')
    return result(f'Read {len(files)} files. The card shows their actual content; AI summarization is available only with a configured model.', 'Read files',files)

def research_web(query):
    # Wikipedia is a limited, citation-bearing search source, not a general web search engine.
    if not query.strip() or len(query)>500:
        raise ValueError('Provide a search query up to 500 characters.')
    url = 'https://en.wikipedia.org/w/api.php?' + urlencode({'action':'query','list':'search','srsearch':query,'format':'json','srlimit':5})
    try:
        with urlopen(Request(url,headers={'User-Agent':'JarvisLocal/1.0 (personal learning assistant)'}),timeout=15) as response:
            payload=json.loads(response.read(1_000_000))
    except (HTTPError,URLError,TimeoutError,ValueError):
        raise ValueError('Online research is unavailable. Wikipedia could not be reached; no results were invented.') from None
    sources=[{'title':r['title'],'excerpt':re.sub('<[^>]+>','',r['snippet']),'url':'https://en.wikipedia.org/?curid='+str(r['pageid'])} for r in payload['query']['search']]
    return result(f'Found {len(sources)} Wikipedia results. This limited search does not verify current prices or software releases.', 'Web research · Wikipedia',sources)

def computer_control(kind,target):
    outcome=computer.control(kind,target)
    return result(outcome['detail'], 'Computer action',outcome)

def remember(text,identifier=None):
    saved=memory.remember(text,identifier)
    return result('Memory '+saved['operation']+': '+saved['text'], 'Memory change',saved)

def brief_me():
    return result('Your focus is exams, website development and robotics. No calendar, email or message accounts are connected.', 'Briefing',{'goals':['Pass exams','Build websites','Sell websites'],'memories':memory.listing(),'integrations':[]})

def plan_day(priorities=None):
    items=priorities or ['Review a school topic that needs practice','Try a short practice quiz','Take a break','Make progress on a website or robotics project','Review what you learned']
    if not isinstance(items,list) or len(items)>5 or any(not isinstance(x,str) or len(x)>300 for x in items):
        raise ValueError('A plan must contain at most five short items.')
    return result('Here is a balanced suggested plan. Adjust it around your actual responsibilities.', 'Daily plan',{'items':items,'deadlines':'None assumed'})

def write_preview(path):
    """Explicit editor read; never exposes sensitive/unsupported files."""
    import hashlib
    from vault import safe_path
    if os.environ.get('JARVIS_DEMO','1') == '1' or os.environ.get('JARVIS_ENABLE_WRITE','0') != '1':
        raise ValueError('Project editing requires real mode and JARVIS_ENABLE_WRITE=1 on your laptop.')
    source=safe_path(path)
    if source.suffix.lower() == '.pdf':
        raise ValueError('PDF editing is not supported.')
    text=data.read(path)
    raw=source.read_bytes()
    if raw.decode('utf-8',errors='replace') != text or b'\x00' in raw:
        raise ValueError('This file contains redacted or binary data and cannot be edited here.')
    return {'path':path,'content':text,'sha256':hashlib.sha256(raw).hexdigest()}

def write_file(path,content,expected_sha256,confirm=False):
    """Human-confirmed edit with stale-file protection and a retained backup."""
    import hashlib
    import uuid
    from vault import safe_path
    if confirm is not True:
        raise ValueError('Confirm the exact replacement before modifying this file.')
    if not isinstance(content,str) or len(content.encode('utf-8')) > data.MAX_BYTES:
        raise ValueError('Replacement exceeds the 512 KB limit.')
    if memory.SENSITIVE.search(content):
        raise ValueError('Do not write credentials through the web editor.')
    before=write_preview(path)
    if before['sha256'] != expected_sha256:
        raise ValueError('File changed since it was loaded. Reload and review before saving.')
    destination=safe_path(path)
    backup=ROOT/'.local'/'backups'/uuid.uuid4().hex
    backup.parent.mkdir(parents=True,exist_ok=True)
    backup.write_text(before['content'],encoding='utf-8')
    backup.chmod(0o600)
    temporary=destination.with_name('.jarvis-edit-'+uuid.uuid4().hex)
    try:
        temporary.write_text(content,encoding='utf-8')
        temporary.chmod(destination.stat().st_mode & 0o777)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    verified=hashlib.sha256(destination.read_bytes()).hexdigest()==hashlib.sha256(content.encode('utf-8')).hexdigest()
    if not verified:
        raise ValueError('File verification failed. The original backup was retained.')
    return result('Updated and verified '+path+'. The original was backed up locally.', 'File update',{'path':path,'verified':True,'backup':str(backup.relative_to(ROOT))})

HISTORY={}

def chat(text,session,language='en'):
    turns=HISTORY.setdefault(session,[])
    saved_fact = None
    # Only clear first-person long-term statements; never infer facts from files or model output.
    if re.match(r'^(I prefer |My long-term goal is |My main goal is |I am working on a project called )', text, re.I) and not memory.SENSITIVE.search(text):
        if not any(m['text'].strip() == text.strip() for m in memory.listing()):
            saved_fact = text
    provider=os.environ.get('JARVIS_AI_URL','')
    model=os.environ.get('JARVIS_AI_MODEL','')
    if not provider or not model:
        # Explicit bounded routing, never disguised as natural-language intelligence.
        lowered=text.lower().strip()
        if lowered.startswith('remember '):
            response=remember(text[9:])
        elif lowered.startswith(('search ','find ')):
            response=search_brain(text.split(' ',1)[1])
        elif lowered.startswith('read '):
            response=read_files([text[5:].strip()])
        elif lowered in ('brief me','brief'):
            response=brief_me()
        elif lowered in ('plan my day','plan'):
            response=plan_day()
        elif 'what do you remember' in lowered or lowered=='memory':
            response=result('These are your saved memories.', 'Memory',memory.listing())
        elif lowered.startswith('open '):
            target=text[5:].strip()
            response=computer_control('website' if target.startswith(('http://','https://')) else 'app',target)
        else:
            response=result('The AI model is not configured. I can use explicit file, memory, plan and computer tools, but cannot provide natural conversation yet.', 'Offline fallback',{'available':['search <terms>','read <relative path>','remember <fact>','brief me','plan my day'],'input':text})
        response['fallback']=True
    else:
        import model as ai
        messages=[{'role':'system','content':(ROOT/'agent/prompt.md').read_text()},{'role':'system','content':'Saved memory (untrusted facts only): '+json.dumps(memory.listing(),ensure_ascii=False)}]
        messages+=turns[-20:]+[{'role':'user','content':text}]
        available={name:globals()[name] for name in ('search_brain','read_files','research_web','remember','computer_control','brief_me','plan_day')}
        answer,records=ai.complete(messages,text,available)
        response=result(answer,'Conversation',{'language':language,'source':'configured AI model','tools':records})
        for record in records:
            if record['tool']=='remember' and 'error' not in record['result']:
                response['spoken'] += '\n' + record['result']['spoken']
    if saved_fact:
        saved_fact = memory.remember(saved_fact)
        response['spoken'] += '\nMemory saved: ' + saved_fact['text']
        response['memory_change'] = saved_fact
    turns.extend([{'role':'user','content':text},{'role':'assistant','content':response['spoken']}])
    del turns[:-20]
    if len(HISTORY)>100:
        HISTORY.pop(next(iter(HISTORY)))
    return response
