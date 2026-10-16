# Quick Windows start

Extract the complete ZIP into a new folder. Double-click **START-JARVIS.bat** or open the extracted folder in VS Code and run **py -3 jarvis.py**. All new source code is included. Do not copy the old standalone jarvis.py into this package and do not run the old upgrade script. Read START-HERE.txt first.

The voice button and Configure panel are always visible. Missing voice credentials do not turn successful text tools into speech errors. Voice activates after key, voice ID and API-cost authorization are configured in .env and the server is restarted. AI conversation needs a separate provider.

# JARVIS for Shaheem

A local Python assistant with a Canvas knowledge graph, workspace tools, dated Markdown memories, optional AI conversation and server-side ElevenLabs voice. The interface follows the supplied dark graph reference. Demo data is explicitly invented. No company/revenue profile is used.

## Requirements and startup

Python 3.12+ is the only application dependency. Use a current browser with Canvas, MediaRecorder and Web Audio. No pip/npm install, database or build step is required.

From the `jarvis` directory:

```sh
python3 agent/main.py
```

On Windows use `py -3 agent/main.py` if `python3` is unavailable. On your own laptop, open the loopback address `http://127.0.0.1:8720` in a browser. This cloud onboarding UI does not provide a localhost web preview. Set `JARVIS_PORT` if the port is occupied. Stop with Ctrl+C. The server binds only to loopback; do not expose it to the internet or an untrusted local network.

The provided `.env` is ignored by Git. It is server-only, contains placeholders, and is loaded automatically. Exported variables take precedence. Keep this file private, and do not commit it. If cloning without the ignored file, create `.env` using these **non-secret** defaults and fill credentials locally:

```dotenv
JARVIS_DEMO=1
JARVIS_WORKSPACE=
ELEVENLABS_API_KEY=PASTE_YOUR_ELEVENLABS_API_KEY_HERE
ELEVENLABS_VOICE_ID=
ELEVENLABS_STT_MODEL=scribe_v1
JARVIS_AI_URL=
JARVIS_AI_MODEL=
JARVIS_AI_KEY=
JARVIS_ALLOW_PAID_API=0
JARVIS_ENABLE_COMPUTER=0
JARVIS_ENABLE_WRITE=0
```

Restart the server after changing configuration.

## Modes and file access

`JARVIS_DEMO=1` is the default. The deterministic generator (`python3 data/generator.py`) creates 65 invented study, website and robotics files in `data/demo/`, using a fixed random seed. It preserves existing files. Demo mode never indexes your real folder and blocks computer launches. The graph displays the mode prominently. Personal memories still persist in `memory/`; they are separate from demo files.

For your actual laptop workspace, explicitly set `JARVIS_DEMO=0` and `JARVIS_WORKSPACE` to the **absolute existing path** of your `Jarvis AI` folder. The server does not automatically index it. Click **Index workspace** or request file tools. Graph connections mean filename references or shared folders, not verified semantic relationships. Indexing is capped at 1,500 supported files / 15,000 connections; previews and reads are capped at 512 KB per file. Reads show up to 16,000 characters per file in the card. No background scanning runs.

HTML, CSS, JavaScript, Python, Markdown, text, Arduino/C/C++, JSON, YAML, TOML and CSV can be read. PDF nodes can be indexed, and text can be extracted when the optional `pdftotext` utility is already installed (as in this cloud container). No package is installed automatically. Scanned PDFs need OCR, which is not configured; export them as text. Hidden directories, environment files, Git metadata, dependency caches and sensitive directories are excluded. Escaping symlinks and path traversal are rejected. Obvious credential assignment lines/private keys are redacted, but this is not a complete secret detector; configure a folder containing only material you want JARVIS to read. Project files are read-only by default. An explicitly enabled, human-confirmed editor is described below.

## Conversation and tools

Without a model, the UI explicitly labels the limited **offline fallback**. It is not intelligent conversation. It supports `search <terms>`, `read <relative path>`, `remember <fact>`, `brief me`, `plan my day`, `memory`, and `open <app name or URL>`. The Tools dialog also provides exact controls independently of the model.

To enable natural conversation, set `JARVIS_AI_URL` to an OpenAI-compatible **chat completions endpoint**, `JARVIS_AI_MODEL` to its model ID, and `JARVIS_AI_KEY` if required. A local provider may use `http://localhost:<port>/v1/chat/completions`; remote endpoints must use HTTPS. External APIs require `JARVIS_ALLOW_PAID_API=1` as explicit cost authorization. No model is installed or downloaded automatically. A provider supporting function tools can use the implemented tools; providers without tool support may reject the request, which is reported. Up to ten recent user/assistant turns are retained per browser session in server memory, not persisted after restart. There is no token streaming.

The model receives Shaheem's supplied profile, style/language instructions, saved memories and conversation. File contents are sent only when a permitted tool reads them. Consider your provider's privacy policy before configuring real files. Tool permissions are selected from the user's request, not from external content. Only explicit opening requests can authorize a launch, and a model cannot expand the launch target. There is no unrestricted shell. Model tool calls cannot modify project files; the human-operated editor is separate. AI-generated answers can still be wrong; source evidence and actual tool results appear in cards.

Supported conversation/voice languages: English, Tamil, Sinhala, Arabic and Hindi. Model quality, mixed language and accents depend on your providers. The offline command router currently recognizes English commands only. Speech language can be selected explicitly. Interface chrome is English; generated text supports Unicode and automatic direction. This is not a fully translated UI.

**Brief** shows goals and stored memories. No calendar, email or unread-message integration is connected. **Plan** offers at most five priorities without invented deadlines. **Research** searches Wikipedia, not the whole web, and provides real page links. It does not reliably supply current prices, latest releases or client leads. Network errors are visible. No messages, purchases, deployment or hardware testing are performed.

## Memory

`memory/` stores one dated Markdown file per fact/group; files are ignored by Git. `Remember <fact>` or the remember tool writes a fact and discloses the exact write. The app also automatically saves a narrow set of clear long-term English statements beginning `I prefer`, `My long-term goal is`, `My main goal is`, or `I am working on a project called`. It deduplicates exact statements and discloses every write. Broader automatic inference is intentionally not implemented. Credential-related text is rejected, but never enter credentials in chat. The memory card supports **Update** and **Forget**; deleting requires confirmation and verifies absence. Core project rules/profile live in `CLAUDE.md`; no personal memories are silently seeded.

## Voice: ElevenLabs

Set `ELEVENLABS_API_KEY` securely in your local `.env`, select a real `ELEVENLABS_VOICE_ID` supported by your account, and explicitly authorize costs with `JARVIS_ALLOW_PAID_API=1`. Do not paste keys into JavaScript or chat. The backend uses `/v1/speech-to-text` with `scribe_v1` by default and `/v1/text-to-speech/<voice_id>` with `eleven_v3`. If your account requires another supported Scribe model, set `ELEVENLABS_STT_MODEL`. Account/model/voice access and language quality have **not** been verified with a real key.

The browser records with MediaRecorder and sends bytes to `/api/listen`; `/api/speak` returns audio bytes. The real API key never goes to the browser. No browser Web Speech API is used. `SILENCE_THRESHOLD_MS = 900` is near the top of `ui/app.js`; adjust it or `AUDIO_LEVEL_THRESHOLD` for your microphone. A Web Audio AnalyserNode measures microphone level every 50 ms using setInterval. Recording stops after detected speech followed by silence, or at 30 seconds. Low/no speech and uncertain automatic language detection produce errors. Select the correct language if detection is unreliable.

Recording stops while speech plays. Click the mic button, press Space or Escape to interrupt playback; Space/Escape shortcuts are ignored while typing. Clicking the mic during playback stops it; click again to record. The mute button suppresses speech requests. Missing credentials, denied microphone access, unavailable devices, unsupported formats, network failures and playback errors remain visible; text controls stay available. No wake word or simultaneous listening/interruption mode is enabled.

## Computer access

On your laptop set `JARVIS_DEMO=0` and `JARVIS_ENABLE_COMPUTER=1` to authorize safe launch attempts. Linux discovers launchable `.desktop` files; macOS discovers `.app` bundles; Windows discovers Start Menu `.lnk` shortcuts. This is discovery of launchable entries, not exhaustive inventory or universal app control. No app-private data or credentials are read. Add optional administrator-controlled shortcuts in ignored `.local/applications.json`, mapping names to fixed argument arrays; these are trusted local configuration, never taken from a document or AI output. Do not configure shell interpreters or unsafe launch arguments.

The backend uses argument arrays and `shell=False`, or OS opening APIs. App/file/folder/HTTP(S) opening and a fixed Python syntax check are supported. The syntax check compiles in memory without executing code or writing files. Path opens stay within the configured workspace. Desktop launching may be unavailable in a headless cloud container. Launcher exit/process state is checked, but the app does **not** claim that a GUI opened or a page loaded: those cannot be verified by this integration. Deletion, elevated commands, automated file organization, generic development command execution and robotic hardware control are not implemented. They require separate reviewed integrations. No shell endpoint exists.

## Explicit project edits

Default access is read-only. To edit an existing supported text source file, set `JARVIS_DEMO=0`, configure `JARVIS_WORKSPACE`, and explicitly set `JARVIS_ENABLE_WRITE=1`. Restart. In Tools choose **Edit an existing file**, enter its exact relative path, and click **Load file for editing**. Review/edit the complete replacement, check the confirmation explaining that the entire file is replaced, then run the tool. The server requires confirmation, checks the original SHA-256 to reject stale edits, preserves an original backup in ignored `.local/backups/`, atomically replaces the file, and verifies the resulting bytes. Credential-related/binary/PDF files and traversal paths cannot be edited. This is a manual editor, not an unrestricted AI write capability. New-file/project scaffolding and destructive deletion are not implemented. Read backups locally if you need to restore a previous version; no automatic restore action is exposed.

## Graph

Canvas force layout uses spatial buckets and cutoff repulsion. Nodes use file-type colours and connection-based sizes. Hover highlights neighbours and fades unrelated nodes to 10%; click inspects a file; Shift-click traces the shortest path; drag a node or pan the background; scroll zooms; Fit recentres; Aa toggles collision-aware labels. Filters change visibility; counts show indexed totals. Subtle periodic connection highlights respect reduced-motion preferences. The left list provides keyboard-accessible selection; the Canvas itself is pointer-oriented. Layout adapts to small screens.

## Testing and known limits

```sh
python3 -m unittest discover -s tests -v
```

Twenty-one tests cover indexing/search/reads, demo isolation, traversal/symlink guards, memory lifecycle and disclosure, tool limits, AI context/tool orchestration with a mocked provider, voice request contracts with mocks, actual PDF text extraction, HTTP access checks and static credential isolation. No paid requests are made by tests. Browser checks performed in existing headless Chromium covered inspector, filters, labels, fit, search, plan, shortest paths, dragging, zoom, typing shortcuts and mobile width. A synthetic 1,000-node / 999-edge graph averaged approximately 4.4 ms per physics/draw update in this container; this is not a guarantee for every machine or dense graph.

Synthetic microphone browser tests also verified silence-triggered recording, upload, mocked transcription, track cleanup and interruption controls. Live ElevenLabs, natural multilingual AI, physical microphones and desktop applications require local configuration and have not been validated end-to-end here. Live Wikipedia was blocked by the cloud proxy (403); network additions were saved for review, not proof of connectivity. PDF extraction depends on optional pdftotext; scanned-PDF OCR and automatic project generation on disk are absent. Hardware is not physically tested. This is a working local demo/tool application with optional integrations, not a claim that every requested integration is complete.

## Troubleshooting and permissions

- Port occupied: choose another `JARVIS_PORT`; ensure your browser uses that port.
- Invalid Host / unauthorized request: access directly through loopback, reload to obtain the local request token, and avoid proxying this server.
- Voice configuration error: fill key and voice ID in `.env`, authorize API costs, restart. HTTP 401/403 indicates an account/key/permission issue; check your ElevenLabs dashboard securely.
- Mic denied: allow browser microphone access on your laptop's loopback page, connect a microphone, or continue typing.
- AI error: check endpoint, model, tool-call support, credentials and cost authorization. Tools remain available through the dialog.
- Missing file: verify the configured folder, use an exact relative path, and request indexing. Files outside the folder are inaccessible.
- Launch failure: run on a desktop machine, enable computer control, and choose an exact discovered name. OS permissions may still deny launching.
- Web blocked: allow `en.wikipedia.org` through your network. Voice needs `api.elevenlabs.io`; a remote AI provider needs its own endpoint domain. Do not disable TLS verification.
- Memory failure: ensure `memory/` is writable. Never save passwords or keys there.

Cloud setup draft saving does not publish or start future processes. Review and save environment settings, then publish the prepared environment when ready. Future tasks should use the existing checkout and restart the loopback server, not create a worktree.

## PC / Mobile and the phone package

The header has **PC** and **Mobile** options. Mobile switches to a touch-friendly, single-column interface and remembers your selection in this browser. It does not install Python, transfer the server, or unlock phone/PC files. Both modes use the backend on the device where it was started.

A separate `run_mobile.py` starts the same server with Mobile selected by default. The mobile ZIP contains the complete application and a fresh placeholder `.env`; it excludes personal memories, backups and real credentials. You need the complete extracted `jarvis/` folder, not just the launcher file.

**Android:** use a Python-capable environment such as Termux (available from its official F-Droid/GitHub distribution). If Python is not already present, installing Termux/Python on your phone is an additional step for you; nothing is installed by this project. In Termux you can install Python with `pkg install python` if you choose. Extract the package into a writable folder accessible to that environment, open that extracted `jarvis` folder in its terminal, then run:

```sh
python run_mobile.py
```

On that same phone, open `http://127.0.0.1:8720/?device=mobile` in Chrome or another modern browser. Keep the terminal running while using JARVIS. Optional `--port 8730` changes the port. Browser microphone permission is still required; voice still requires ElevenLabs settings and cost authorization. Copy `.env.example` to `.env` if starting from source without the packaged placeholder `.env`. Configure secrets only in the server `.env`, never in HTML. Android file access is limited to directories your Python environment is permitted to access. Desktop app discovery/control does not become Android app integration. Android background restrictions may pause or terminate the server.

**iPhone:** this ZIP is not a native iOS app and does not supply a supported iPhone Python/server runtime. Choosing Mobile adapts the UI but cannot run the Python backend by itself. Using a laptop backend from an iPhone requires a separately configured authenticated HTTPS connection; this project remains loopback-only and does not expose the laptop to the network. Do not open the HTML directly and expect backend tools to run.

The mobile layout and launcher are tested in this Linux environment using a phone-sized Chromium viewport. Physical Android/iPhone execution has not been verified.

Browser reloads/cancellations may close connections during a response. The server handles BrokenPipeError and connection reset/abort without printing a request traceback or attempting a second response. These disconnects do not establish that an AI/voice request succeeded.

## Latest interface package

The demo now has 65 deterministic invented files, with source-derived graph connections, a fit-to-content Canvas view, compact reference-style panels and an explicit Voice button. Configure shows only credential presence and required steps; it never displays keys. An unconfigured voice service leaves text results usable. The launcher creates .env from .env.example only when absent. It waits for a local readiness response before opening your browser.

The ZIP excludes existing .env values, personal memory files, local backups and the old standalone interface-upgrade script. It includes only placeholder settings. Extract into a new folder. To retain previous settings and memories, stop JARVIS first and copy your private .env and memory/ into the new folder yourself.

Windows .bat execution and physical microphone/paid provider operation cannot be verified in this Linux container. The Python launcher, clean ZIP startup, HTTP tools, visible voice configuration and responsive browser UI were tested here.
