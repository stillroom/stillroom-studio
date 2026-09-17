# Stillroom Studio

A local creative workspace for making social media assets with your brand, editable copy, and AI-generated imagery. Studio connects to an existing Hermes installation for authorised models, profiles, and writing skills.

The image model creates the background; Studio draws the text separately, so copy and layout changes appear immediately without regenerating the image. Projects and media are saved on the computer running Studio. AI requests are sent to the providers configured in Hermes.

## Contents

- [Features](#features)
- [Requirements](#requirements)
- [Quick start](#quick-start)
- [Using Studio](#using-studio)
- [Configuration](#configuration)
- [Hermes and skills](#hermes-and-skills)
- [Storage and backups](#storage-and-backups)
- [Moving or installing elsewhere](#moving-or-installing-elsewhere)
- [Local network access](#local-network-access)
- [MCP integration](#mcp-integration)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Scope and limitations](#scope-and-limitations)

## Features

- Campaign and photoshoot workflows with a brief, art direction, and optional custom instructions.
- Three suggested campaign directions using your message and uploaded source material.
- Editable headlines, supporting copy, calls to action, captions, crop, shading, and typography.
- Brand room for identity, voice, colours, and exclusions.
- Social format presets, adjustable safe areas, and PNG/JPG export.
- Full-image preview with independent editor scrolling, zoom, and drag-to-pan inspection.
- Saved creative library and a context-aware Studio assistant with Markdown responses.
- Separate Hermes profile and skill selections for campaign writing and assistant chat.
- Local HTTP API and an MCP adapter for other clients.

## Requirements

| Component | Requirement |
| --- | --- |
| Runtime | Python 3.10 or newer; Bash for `start.sh` |
| Browser | A modern browser with Canvas support |
| AI features | A compatible Hermes installation with its Python environment, profiles, and provider authentication configured |
| PDF text import | `pdftotext` on `PATH` (provided by Poppler); no OCR is performed |
| Building or developing | Node.js 22.13 or newer and npm |

The current launcher and Hermes environment paths are designed for Linux/POSIX. Native Windows installation needs adjustments, including Hermes' Python executable path. Other operating systems have not been verified.

Hermes is an external dependency, not bundled with Studio. The adapter uses its internal provider and text-generation interfaces; a significant Hermes upgrade may require adapter changes. The prebuilt app does not need Node or `node_modules` to run.

## Quick start

Run commands from the Studio directory unless stated otherwise.

### From a complete app copy

If `dist/client/index.html` is present:

```bash
bash start.sh
```

Open [http://127.0.0.1:8787](http://127.0.0.1:8787). Keep the terminal open while using Studio; press **Ctrl+C** to stop it.

### From a source checkout

Build the frontend first:

```bash
npm ci --ignore-scripts
npm run build
bash start.sh
```

`dist/` and `data/` are excluded from Git. A source checkout therefore needs a build and starts with a fresh workspace unless you restore a backup.

Open **Hermes** in Studio to select a campaign profile, image provider, image model, and optional assistant settings. Only providers available through the selected Hermes profile are listed. Configure missing provider credentials in Hermes, then refresh Studio.

## Using Studio

1. In **Brand room**, enter your brand's identity, voice, colours, and exclusions.
2. In **Create**, choose Campaign or Photoshoot and write your message and scene direction.
3. Upload PNG, JPEG, WebP, PDF, TXT, or MD source material. Select image ingredients when they should be sent as visual references.
4. Use **Find three campaign directions** for suggested copy, or enter your own wording.
5. Select an image model and generate an image. Generation uses that provider's allowance or billing.
6. Adjust the copy and layout, inspect the safe areas, and export PNG or JPG. Preview guides are excluded from exports.

Photoshoot mode hides the text. To request an image edit, select an uploaded image as an ingredient and describe the desired change in the scene or additional direction.

### Preview versus crop

The complete image is the default preview. The compact zoom control below it ranges from 100% to 800% of the fitted view. Use the slider, plus/minus buttons, mouse wheel over the image, or **+ / −** keys when not typing. Drag to inspect an enlarged image. Press **0** or **Full image** to reset the view. Preview zoom does not affect exports.

**Layout → Crop zoom** changes the image inside the composition and affects exports. Moving either crop axis ensures at least 115% crop zoom so the image can move without exposing blank edges. **Reset crop** restores a centred cover fit.

| Export format | Dimensions |
| --- | --- |
| Reels / TikTok and Stories | 1080 × 1920 |
| Portrait feed | 1080 × 1350 |
| Square | 1080 × 1080 |
| Landscape | 1920 × 1080 |

Safe areas are editable design presets, not guaranteed platform specifications. Text is measured, wrapped, and reduced to fit; unresolved text overflow blocks export. The preview and exports use the same Canvas renderer.

### Studio assistant

Open **Studio assistant** from any page. Its context follows the current page: active creative, saved library, brand, or configuration. Choose its own profile and skills under **Hermes → Studio assistant**. Changes apply to the next message without clearing the conversation.

Suggestions remain in chat until you choose to use them. Skills guide responses as text instructions; the assistant does not execute their tools or take external actions.

## Configuration

Export environment variables in the shell before starting Studio. Studio does not automatically load an app-local `.env` file. The Hermes adapter separately loads Hermes' environment files.

| Variable | Default | Purpose |
| --- | --- | --- |
| `HERMES_ROOT` | `~/.hermes/hermes-agent` | Hermes source installation; must contain `venv/bin/python` |
| `STUDIO_HERMES_HOME` | `~/.hermes` | Hermes configuration, profiles, and shared skills |
| `STUDIO_DATA` | `data/` inside the app directory | Studio workspace, uploads, generated media, and provider cache |
| `STUDIO_TOKEN` | Unset | Access token for API/media requests; required for LAN hosting |
| `STUDIO_URL` | `http://127.0.0.1:8787` | Server address used by the MCP adapter only |

Use absolute paths for path overrides. For example:

```bash
export HERMES_ROOT="/path/to/hermes-agent"
export STUDIO_HERMES_HOME="/path/to/hermes-home"
export STUDIO_DATA="/path/to/studio-data"
bash start.sh --port 8787
```

The server accepts `--host` and `--port`. Its defaults are `127.0.0.1` and `8787`. Changing the port also requires updating the MCP URL and, for development, the proxy target in `vite.config.ts`.

## Hermes and skills

Studio discovers profiles and authorised image models from Hermes at runtime. Model options depend on the installed Hermes plugins and the selected profile's authentication; Studio does not maintain a separate fixed model catalogue.

Campaign copy uses the campaign profile's text model. Assistant chat uses its independently selected profile. Image generation uses the chosen provider and model. Each adapter request runs in a fresh subprocess, keeping Studio selections separate from running Hermes sessions.

Studio does not edit Hermes source or configuration. Provider authentication stays with Hermes, including normal credential refresh; Studio does not copy keys into the browser.

Only skills in this shared directory are listed:

```text
~/.hermes/skills/stillroom-studio/
├── campaign-copy/
│   └── SKILL.md
└── brand-voice/
    └── SKILL.md
```

The names above are examples, not bundled skills. Create one subfolder and `SKILL.md` per skill. With a custom Hermes home, use `STUDIO_HERMES_HOME/skills/stillroom-studio/`. Hermes can read and write these same files. The `skills/` folder in the Studio repository is a pointer to this shared location.

**Browse Hermes conversations** reads existing gateway conversations through `hermes mcp serve`. Selecting a conversation imports it as reference material; Studio does not send messages to external channels.

## Storage and backups

| Location | Contents |
| --- | --- |
| `data/workspace.json` | Brand, active creative, saved library entries, source text, chat, and selected settings |
| `data/media/` | Uploaded and generated image files |
| `data/provider-cache/` | Provider-generated media cache |
| `public/references/` | Bundled reference imagery used by the app |
| `dist/client/` | Built frontend served in production |

`STUDIO_DATA` overrides the first three locations. Changes autosave; wait for **Saved locally** before stopping or moving the app. Jobs are held in memory and do not survive a server restart.

To back up, finish active jobs, stop Studio, and copy the entire data directory. Back up shared Studio skills separately from Hermes. To restore, stop Studio and place the backed-up data at the configured data location before restarting.

**Export project manifest** downloads metadata, not image bytes, and is not a complete backup. Removing a creative from the library retains its image file because other references may use it.

## Moving or installing elsewhere

### Move on the same computer

1. Wait for saves and active jobs to finish, then stop Studio.
2. Move the entire app directory, including `dist/client`, `public`, and `data`.
3. Update shortcuts, service definitions, or MCP configurations that contain the old path.
4. Run `bash start.sh` from the new directory.

App paths resolve relative to the installation. An external `STUDIO_DATA` directory remains where it is until you move it and update the override. Hermes and its shared skills remain in their own locations.

### Install on another computer

1. Install Python and a compatible Hermes setup on the destination, and authenticate the required providers there.
2. Copy the complete app directory, or copy the source and build it using the quick-start instructions.
3. Restore `data/` if you want the existing workspace, and copy the shared `stillroom-studio` skills folder separately.
4. Set path overrides if Hermes or Studio data use different locations.
5. Start Studio and check profile/model selections on its Hermes page.

For a prebuilt transfer, `node_modules` is unnecessary. Install build dependencies afresh if developing on the destination. Set up Hermes' environment there rather than treating its existing Python virtual environment as portable.

## Local network access

Other devices can use the browser interface while Studio and Hermes remain on one host. Start the server with a token of at least 24 characters:

```bash
export STUDIO_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
bash start.sh --host 0.0.0.0 --port 8787
```

Open `http://HOST-LAN-IP:8787` on the other device. Enter the same token under **Hermes → Local network access**. The generated token is in the launching shell's environment; retain it securely for connecting clients. Rerunning the generation command creates a new token.

The token protects API requests and uploaded/generated media and is stored in the browser tab's session storage. The static app shell and bundled reference assets are not token-protected. HTTP does not encrypt traffic; use a trusted private network, or an HTTPS reverse proxy when encryption is required. This server is not intended for direct public internet exposure.

One server has one shared workspace. Concurrent edits can overwrite each other; the last save wins. There are no separate user accounts or independent workspaces per browser.

## MCP integration

Studio provides a stdio MCP adapter that calls its running HTTP server. Add the following to your MCP client's configuration, replacing the path:

```json
{
  "mcpServers": {
    "stillroom-studio": {
      "command": "python3",
      "args": ["/absolute/path/to/stillroom-studio/studio/mcp.py"]
    }
  }
}
```

For a different server address or a protected server, add `STUDIO_URL` and `STUDIO_TOKEN` to that MCP entry's environment. Studio does not install this configuration automatically.

| Tool | Result |
| --- | --- |
| `studio_workspace` | Current workspace data |
| `studio_catalog` | Job ID for profile, provider, model, and skill discovery |
| `studio_generate` | Job ID for image generation; consumes provider usage |
| `studio_job` | Status and result of a submitted job |

Poll `studio_job` after catalogue or generation requests. Generated results contain a server-relative image URL. MCP generation does not automatically replace the active creative in the browser.

## Development

The frontend uses React, TypeScript, Vinext/Vite, and Tailwind CSS. Production serves a static export through a Python standard-library HTTP server; Hermes provides the AI runtime.

```text
app/                 Main interface and styles
components/ui/       Shared UI components
lib/studio.ts        Creative types, prompt composition, Canvas layout/export
studio/server.py     HTTP API, persistence, uploads, and asynchronous jobs
studio/hermes_bridge.py  Isolated Hermes adapter
studio/mcp.py        MCP stdio adapter
public/references/   Bundled image assets
skills/              Shared-skill location documentation
tests/               Python backend and JavaScript layout checks
start.sh             Production launcher
```

Install dependencies with `npm ci --ignore-scripts`. Run these in separate terminals:

```bash
# Terminal 1: API server
python3 studio/server.py
```

```bash
# Terminal 2: frontend development server
npm run dev
```

Open the development URL printed by Vite. The development server proxies `/api` and `/media` to `127.0.0.1:8787`. Use the production launcher for normal use.

Before submitting changes:

```bash
npm run typecheck
npm test
npm run build
```

Tests cover Canvas layout, crop geometry, prompts, upload validation, path confinement, origin/token checks, persistence, jobs, and skill scoping. They do not establish live provider availability or replace visual review. `npm run lint` is also available; `npm run format` rewrites formatting.

After frontend changes, rebuild and refresh the production browser. Restart the server after `studio/server.py` changes. The Hermes adapter is loaded afresh for each request. Keep workspace data, credentials, and generated build files out of source commits, as configured in `.gitignore`.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Launcher asks for a build | Run `npm ci --ignore-scripts` and `npm run build`; confirm `dist/client/index.html` exists. |
| Port is already in use | Stop the other instance or use `bash start.sh --port 8788`. |
| Hermes adapter cannot start | Check `HERMES_ROOT` and its `venv/bin/python`, plus Hermes' installed dependencies. |
| An image provider/model is missing | Check the campaign profile, Hermes plugin catalogue, and provider authentication, then refresh Studio. |
| Skills are missing | Put each `SKILL.md` inside a subfolder of the shared Studio skills directory and refresh. |
| PDF import fails or has no text | Check `pdftotext` on `PATH`; provide TXT/MD for scans or PDFs without extractable text. |
| Access token required | Enter the current server token; check the hostname/origin and MCP token configuration. |
| Generated media is missing after a move | Restore the full data directory and check `STUDIO_DATA`, not just the JSON manifest. |
| Job expired or server restarted | Job state is temporary. Check the workspace/library before starting another generation. |
| UI still shows an old version | Rebuild the frontend if changed, then refresh the browser. |

For a local default server, `curl http://127.0.0.1:8787/api/health` checks server response and whether the expected Hermes Python executable exists. It does not test credentials or model access.

## Scope and limitations

Uploads are limited to 20 MB per file. Source text extraction is capped at 60,000 characters per document. The interface accepts up to three selected image references, subject to provider capabilities. Source material is included in relevant AI requests; local storage does not mean offline generation.

Studio does not scrape websites, publish social posts, generate videos, perform OCR, or produce brand books. It is a personal/shared local workspace, not a multi-tenant service or a packaged desktop installer.

The workflow was informed by Pomelli and user-supplied reference imagery, while focusing on editable copy and social-safe layouts. Reference assets should be reviewed for redistribution rights before sharing the repository publicly. No repository licence file is currently included.
