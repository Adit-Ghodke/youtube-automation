# YouTube Automation Agent

> **AI-powered YouTube video factory** — generates script, narration, segment-matched video, background music, thumbnail, and uploads to YouTube from a single text prompt.

AI-powered video automation with 7 pipeline stages + RAG-enhanced scripts + segment-matched video assembly + real stock footage (Pexels API), built with Python, Groq AI (Llama 3.3 70B), MoviePy 2.x, Edge-TTS, and ChromaDB. Local execution with YouTube Data API v3 upload.

**Built using Vibe Coding** — AI-assisted rapid development with GitHub Copilot for architecture, code generation, optimization, and iterative refinement. See the [Build Plan](BUILD_PLAN.md) for methodology details.

---

## Features (7 Pipeline Stages + 6 Enhancements)

### Pipeline Stages (7)
| # | Stage | Description |
|---|-------|-------------|
| 1 | **AI Script Generation** | Groq LLM (Llama 3.3 70B → 3.1 8B → Mixtral fallback) with RAG-enhanced prompts. 5 storytelling styles: Narrative Journey, Mystery Reveal, Documentary, Discovery, Problem-Solution |
| 2 | **RAG Knowledge Retrieval** | ChromaDB vector search with JSON keyword fallback. 30+ curated facts across science, space, psychology, technology, nature |
| 3 | **Neural Text-to-Speech** | Edge-TTS (Microsoft neural voices) with 10+ voice options, configurable rate and pitch |
| 4 | **Segment-Matched Video Assembly** | Per-segment Pexels API search → each script segment gets visually matching HD clips → duration-matched cutting → ordered assembly |
| 5 | **Background Music Mixing** | Royalty-free ambient music from FreePD.com mixed at configurable volume (default 15%) with narration |
| 6 | **AI Thumbnail Generation** | Auto-generated via Pollinations.ai (free, no API key) based on video title |
| 7 | **YouTube Upload** | Automated upload with title, description, tags, hashtags, category, and thumbnail via YouTube Data API v3 |

### Enhancements (6)
| # | Enhancement | Description |
|---|-------------|-------------|
| 8 | **Parallel Downloads** | ThreadPoolExecutor with configurable workers (default 5) for 3x faster video fetching |
| 9 | **Speed Optimized Encoding** | `ultrafast` preset + 12 CPU threads + `chain` concatenation + `fastdecode` tuning |
| 10 | **YouTube Shorts Support** | Vertical 9:16 format (1080×1920) with auto `#Shorts` tag and ≤60s duration |
| 11 | **Multiple Voice Options** | 10+ Edge-TTS voices (male/female, US/UK/AU/IN accents) with speed and pitch controls |
| 12 | **Content Calendar** | JSON-based scheduling and tracking of published videos |
| 13 | **Metrics & Monitoring** | Performance tracking, API health checks, email alerts for failures |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **AI Engine** | Groq API (Llama 3.3 70B Versatile) via OpenAI-compatible client |
| **RAG** | ChromaDB ≥0.4.0 + Sentence Transformers ≥2.2.0 (JSON keyword fallback) |
| **Text-to-Speech** | Edge-TTS ≥7.2.0 (Microsoft neural voices, async) |
| **Video Editing** | MoviePy ≥2.2.0 + Pillow ≥9.2.0 + FFmpeg |
| **Stock Footage** | Pexels API (free, HD video search with orientation filter) |
| **Background Music** | FreePD.com (royalty-free ambient tracks, no API key) |
| **Thumbnails** | Pollinations.ai (free AI image generation, no API key) |
| **YouTube Upload** | Google API Python Client ≥2.188.0 + OAuth2 |
| **Concurrency** | concurrent.futures.ThreadPoolExecutor |
| **Config** | JSON (`config.json`) + python-dotenv (`.env`) |
| **Scheduling** | schedule ≥1.2.2 (periodic automated runs) |
| **Logging** | RotatingFileHandler (10 MB, 5 backups, UTF-8) |

---

## Quick Start (Local Development)

The fastest way to get started on Windows:

```batch
# 1. Run the automated setup
setup.bat

# 2. Edit .env with your actual API keys
# 3. Run (single video)
python main.py
```

Manual setup (if `setup.bat` is not used):
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python main.py --topic "5 mind-blowing facts about the ocean"
```

---

## Project Structure

```
Youtube automation/
├── main.py                      # Entry point — CLI, scheduling, orchestration
├── youtube_automation_agent.py  # Core pipeline — script → audio → video → upload (758 lines)
├── rag_engine.py                # RAG engine — ChromaDB + JSON fallback (264 lines)
├── config.json                  # All runtime configuration (21 options)
├── requirements.txt             # Python dependencies (10 packages)
├── setup.bat                    # One-click Windows setup script
│
├── content_calendar.py          # Content scheduling & publish tracking
├── metrics_tracker.py           # Performance & cost metrics (JSON-backed)
├── health_check.py              # Pre-run API health verification (Groq, Pexels, Edge-TTS)
├── alerts.py                    # SMTP email alert system for failures
├── logger_config.py             # Rotating file + console logger (UTF-8)
├── test_rag.py                  # RAG engine verification script
│
├── .env                         # API keys (gitignored)
├── .env.example                 # Template for .env
├── .gitignore                   # Git ignore rules
├── youtube_credentials.json     # Google OAuth2 credentials
├── token.pickle                 # Cached auth token (gitignored)
│
├── rag_data/                    # RAG knowledge base storage
├── output/                      # Generated videos, thumbnails, audio
└── logs/                        # Rotating log files
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Groq API key — free at [console.groq.com/keys](https://console.groq.com/keys) |
| `PEXELS_API_KEY` | Yes | Pexels API key — free at [pexels.com/api](https://www.pexels.com/api/) |
| `YOUTUBE_CREDENTIALS_PATH` | No | Path to YouTube OAuth credentials (default: `./youtube_credentials.json`) |

---

## Configuration (`config.json`)

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `niche` | string | `"educational facts and science"` | Content niche used in AI prompt |
| `target_audience` | string | `"curious minds..."` | Audience description for tone calibration |
| `video_style` | string | `"Fast-paced..."` | Visual/editing style description |
| `tone` | string | `"enthusiastic and mind-blowing"` | Script tone |
| `video_duration` | int | `90` | Target video length in seconds |
| `fps` | int | `30` | Frames per second |
| `format` | string | `"standard"` | `standard` (16:9) or `shorts` (9:16) |
| `resolution` | string | `"1080p"` | `1080p` or `720p` (lower = faster) |
| `voice` | string | `"en-US-AriaNeural"` | Edge-TTS voice ID |
| `voice_rate` | string | `"+0%"` | Speaking speed (-50% to +100%) |
| `voice_pitch` | string | `"+0Hz"` | Voice pitch (-50Hz to +50Hz) |
| `add_music` | bool | `true` | Enable background music |
| `music_volume` | float | `0.15` | Background music volume (0.0–1.0) |
| `generate_thumbnail` | bool | `true` | Auto-generate AI thumbnail |
| `parallel_downloads` | bool | `true` | Use ThreadPoolExecutor |
| `max_download_workers` | int | `5` | Parallel download threads |

### Available Voices (Edge-TTS)

| Voice ID | Gender | Accent |
|----------|--------|--------|
| `en-US-AriaNeural` | Female | American |
| `en-US-GuyNeural` | Male | American |
| `en-GB-SoniaNeural` | Female | British |
| `en-GB-RyanNeural` | Male | British |
| `en-AU-NatashaNeural` | Female | Australian |
| `en-IN-NeerjaNeural` | Female | Indian |
| `en-IN-PrabhatNeural` | Male | Indian |

---

## Usage

```bash
# Single video with custom topic
python main.py --run-once --topic "the science of black holes"

# Single video with default topic (uses niche from config.json)
python main.py --run-once

# Scheduled: create a new video every 6 hours
python main.py --schedule "6 hours"

# YouTube Shorts mode (set "format": "shorts" in config.json first)
python main.py --run-once --topic "Did you know this about ants?"

# Test RAG engine
python test_rag.py
```

---

## Architecture Highlights

- **Segment-Matched Video Pipeline** — Each script segment gets its own Pexels search using that segment's `video_keywords`, clips cut to match speaking duration, assembled in script order
- **RAG-Enhanced Scripts** — 30+ curated facts injected into LLM prompts for factual accuracy; ChromaDB vector search with graceful JSON keyword fallback
- **Multi-Model Fallback** — Groq API tries Llama 3.3 70B → Llama 3.1 8B → Mixtral 8x7B automatically on failure
- **5 Storytelling Styles** — AI randomly picks Narrative Journey, Mystery Reveal, Documentary, Discovery, or Problem-Solution format (no more monotonous "5 Facts" videos)
- **Speed Optimized** — Parallel downloads (ThreadPoolExecutor), `chain` concatenation (3x faster than `compose`), `ultrafast` FFmpeg preset, 12-thread CPU encoding
- **Deep AI Prompts** — Structured prompt with hook/body/climax/CTA sections, specific video keyword rules, and segment-based JSON output format
- **Graceful Degradation** — ChromaDB → JSON fallback (silent), Llama 70B → 8B → Mixtral fallback, background music retry (multiple sources) → narration only, AI thumbnail retry → Pexels fallback.
- **Portable Setup** — Bulletproof `setup.bat` with Python/FFmpeg checks, automatic `.env` creation, and individual package installation fallback.
- **Clean Execution** — Suppressed internal warnings and explicit file lock handling for a zero-error console output.

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `quotaExceeded` error | YouTube daily API limit (10,000 units) | Wait 24h. Video is still saved in `output/final_video.mp4` |
| `Missing API keys` error | Blank or placeholder keys in `.env` | Run `setup.bat` or edit `.env` with real keys from Groq/Pexels |
| `FFmpeg not found` | FFmpeg missing from system PATH | Install via `winget install Gyan.FFmpeg` as prompted by `setup.bat` |
| `ChromaDB failed` | Python 3.14+ compatibility | Handled automatically. JSON fallback activates silently |
| `Thumbnail upload fails` | YouTube channel not verified | Verify at [youtube.com/verify](https://youtube.com/verify) |

---

## License

This project is for educational and academic purposes only.
