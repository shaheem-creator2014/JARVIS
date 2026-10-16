"""Server-only ElevenLabs HTTP integration using standard library."""
import json
import os
import uuid
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
LANGUAGES = {'en':'eng','ta':'tam','si':'sin','ar':'ara','hi':'hin'}

def status():
    key = os.environ.get('ELEVENLABS_API_KEY', '')
    key_present = bool(key and key != 'PASTE_YOUR_ELEVENLABS_API_KEY_HERE')
    voice_present = bool(os.environ.get('ELEVENLABS_VOICE_ID', '').isalnum())
    costs_allowed = os.environ.get('JARVIS_ALLOW_PAID_API', '0') == '1'
    missing = []
    if not key_present:
        missing.append('Add ELEVENLABS_API_KEY to .env')
    if not voice_present:
        missing.append('Set ELEVENLABS_VOICE_ID in .env')
    if not costs_allowed:
        missing.append('Authorize possible API costs with JARVIS_ALLOW_PAID_API=1')
    return {'ready': not missing, 'key_present': key_present,
            'voice_present': voice_present, 'costs_allowed': costs_allowed,
            'message': '; '.join(missing) + '. Restart JARVIS after changes.' if missing
            else 'Configured locally. Account and voice will be checked on your first request.'}

def configuration():
    key = os.environ.get('ELEVENLABS_API_KEY','')
    if not key or key == 'PASTE_YOUR_ELEVENLABS_API_KEY_HERE':
        raise ValueError('ElevenLabs is not configured. Enter a real ELEVENLABS_API_KEY in the server .env file. Text interaction remains available.')
    if os.environ.get('JARVIS_ALLOW_PAID_API','0') != '1':
        raise ValueError('Voice API calls may cost money. Set JARVIS_ALLOW_PAID_API=1 only after authorizing those costs.')
    return key

def request(path, body, content_type):
    req = Request('https://api.elevenlabs.io/v1/' + path, data=body, headers={'xi-api-key':configuration(),'Content-Type':content_type})
    try:
        with urlopen(req, timeout=35) as response:
            result = response.read(12_000_001)
            if len(result) > 12_000_000:
                raise ValueError('Voice response exceeds the size limit.')
            return result
    except HTTPError as exc:
        raise ValueError(f'ElevenLabs returned HTTP {exc.code}. Check key, account permissions, model and voice settings.') from None
    except (URLError, TimeoutError):
        raise ValueError('ElevenLabs could not be reached. Check your connection; text interaction remains available.') from None

def listen(audio, mime, language):
    if language not in LANGUAGES and language != 'auto':
        raise ValueError('Unsupported recognition language.')
    if not audio or len(audio) > 8_000_000:
        raise ValueError('Audio must be nonempty and below 8 MB.')
    mime = mime.split(';')[0]
    if mime not in ('audio/webm','audio/ogg','audio/mp4','audio/wav'):
        raise ValueError('Unsupported recording format.')
    boundary = uuid.uuid4().hex
    body = bytearray()
    fields = {'model_id':os.environ.get('ELEVENLABS_STT_MODEL','scribe_v1'), 'tag_audio_events':'false'}
    if language != 'auto':
        fields['language_code'] = LANGUAGES[language]
    for name, value in fields.items():
        body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    extension = {'audio/webm':'webm','audio/ogg':'ogg','audio/mp4':'m4a','audio/wav':'wav'}[mime]
    body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="speech.{extension}"\r\nContent-Type: {mime}\r\n\r\n'.encode())
    body.extend(audio)
    body.extend(f'\r\n--{boundary}--\r\n'.encode())
    result = json.loads(request('speech-to-text',bytes(body),'multipart/form-data; boundary='+boundary))
    if not result.get('text','').strip():
        raise ValueError('No reliable speech was recognized. Please repeat or select a language.')
    confidence = result.get('language_probability')
    if language == 'auto' and (result.get('language_code') not in LANGUAGES.values() or confidence is not None and confidence < .65):
        raise ValueError('Language could not be reliably identified. Please select your language and repeat.')
    return {'text':result['text'], 'language':result.get('language_code'), 'confidence':confidence}

def speak(text, language):
    if language not in LANGUAGES:
        raise ValueError('Select a supported speech language.')
    voice = os.environ.get('ELEVENLABS_VOICE_ID','')
    if not voice or not voice.isalnum():
        raise ValueError('Set ELEVENLABS_VOICE_ID to an available voice for your account.')
    if not text or len(text) > 3000:
        raise ValueError('Speech text must contain 1–3000 characters.')
    payload = {'text':text,'model_id':'eleven_v3','language_code':language}
    return request('text-to-speech/'+voice,json.dumps(payload).encode(),'application/json')
