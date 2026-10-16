# JARVIS — Shaheem's personal assistant

A local Python assistant with a dark Canvas knowledge graph, file tools, persistent memory, optional AI conversation, and ElevenLabs voice. Demo mode is the default. No extra Python packages or frontend build tools are required.

## Download and run on Windows

1. On this GitHub page, click **Code → Download ZIP**.
2. Right-click the downloaded ZIP and choose **Extract All**.
3. Open the extracted folder, then open its **jarvis** folder.
4. Double-click **START-JARVIS.bat**. Keep its terminal open.
5. Brave or Chrome opens when the local server starts. If needed, enter `http://127.0.0.1:8720`.

Python 3.12 or newer is required. In VS Code, open the **jarvis** folder and run:

```powershell
py -3 jarvis.py
```

The latest application source is already included. You do not need to paste an older standalone script or run an interface-upgrade script.

## Try it

- `search Arduino`
- `read studies/fractions.md`
- `remember I prefer clear explanations`
- `plan my day`

The graph displays 65 invented demo documents. Click nodes to inspect them; Shift-click to trace a path. Drag to pan, scroll to zoom, and use the file filters. **PC / Mobile** changes the layout. It does not transfer the server to another device.

## Voice and natural conversation

The **Voice** button and its **Setup** panel show what configuration is missing. On first launch, the app creates a private `.env` from `.env.example`. Enter your ElevenLabs key and voice ID **only in .env**, and authorize possible API charges only if you choose. Restart after changing settings. Real credentials are never included in this repository.

ElevenLabs provides speech recognition and synthesis. Natural conversation requires a separate OpenAI-compatible AI provider; without one, the interface clearly labels its limited offline tools. No email, calendar or messaging accounts are connected.

Read [the full setup and limitations](jarvis/README.md) or [the short Windows guide](jarvis/START-HERE.txt). On Android with Python already available, run `python run_mobile.py` from the **jarvis** folder.

## Validation

From the **jarvis** folder:

```powershell
py -3 -m unittest discover -s tests -v
```

The current version passed 21 backend tests, clean-package startup, browser layout/interaction checks, and synthetic microphone tests with mocked transcription. Live paid AI/voice requests and physical Windows/phone integrations still require local configuration and testing.

Personal memories, real `.env` values, demo outputs, and local backups are excluded from Git. Extract new versions into a new folder so your older settings and memories remain intact.
