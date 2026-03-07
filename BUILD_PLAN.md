**Project:** YouTube Automation Agent  
**Version:** v2.1 (March 2026)  
**Tech Stack:** Python 3.12 + Groq API (Llama 3.3 70B) + Pexels API (stock video) + Edge-TTS (neural voices) + MoviePy 2.x + ChromaDB (RAG) + YouTube Data API v3 + Pollinations.ai (thumbnails) + FreePD.com (music)  
**Built With:** Vibe Coding — AI-assisted rapid development using GitHub Copilot for architecture, code generation, optimization, and iterative refinement  
**Target:** Fully functional AI video factory — single prompt to published YouTube video

---

## Development Methodology: Vibe Coding

This project was built using **Vibe Coding** — an AI-assisted development approach where the developer collaborates with an AI coding agent in an iterative, conversational workflow.

### How This Project Was Built

| Phase | Human Role | AI Role |
|---|---|---|
| **Architecture** | Described video automation vision, chose APIs | Designed pipeline, module structure, data flow |
| **Implementation** | Reviewed code, tested outputs, caught edge cases | Generated all Python code across 10 modules (758+ lines core agent) |
| **Integration** | Provided API keys, tested real services | Wired Groq + Pexels + Edge-TTS + YouTube + Pollinations + FreePD |
| **Optimization** | Requested faster rendering, better video matching | Implemented parallel downloads, chain concatenation, segment-matched pipeline |
| **RAG System** | Curated 30+ knowledge facts | Built ChromaDB + JSON fallback, prompt injection |
| **Refinement** | Iterated on video quality and script diversity | Rewrote prompts for 5 storytelling styles, added segment-matched clips |

## IMPORTANT — Use Context7 for Latest Tech

Before implementing any feature or upgrading any dependency, use **Context7** to fetch the latest official documentation and code examples for:
- **MoviePy** — `concatenate_videoclips`, `CompositeAudioClip`, `write_videofile` parameters (v2.x broke many v1.x APIs)
- **Edge-TTS** — `Communicate` class, voice list, rate/pitch formatting
- **ChromaDB** — Client initialization, collection creation, query methods
- **Sentence Transformers** — Model loading, encoding
- **google-api-python-client** — YouTube upload, thumbnail set
- **Groq Python SDK** — Chat completions (OpenAI-compatible)

**This is mandatory.** At the start of each phase, verify package versions and implementation examples from Context7, then apply that guidance in code.

**Execution Rule:** MoviePy 2.x changed `subclip()` → `subclipped()`, removed several methods, and changed import paths. Context7 prevents hours of debugging from outdated Stack Overflow answers.

---

## 1) Build Strategy

### Development Timeline

| Phase | Estimated Time | Description |
|-------|---------------|-------------|
| Phase 0 | 15 min | Prerequisites, environment, project scaffold |
| Phase 1 | 30 min | RAG engine (ChromaDB + JSON fallback) |
| Phase 2 | 45 min | Script generation (Groq LLM + RAG prompts) |
| Phase 3 | 20 min | Audio generation (Edge-TTS neural voices) |
| Phase 4 | 45 min | Segment-matched video pipeline (Pexels API) |
| Phase 5 | 30 min | Video composition + background music |
| Phase 6 | 20 min | AI thumbnail generation (Pollinations.ai) |
| Phase 7 | 30 min | YouTube upload (OAuth2 + Data API v3) |
| Phase 8 | 20 min | CLI interface + scheduling + orchestration |
| Phase 9 | 20 min | Supporting modules (health, metrics, calendar, alerts) |
| Phase 10 | 30 min | Speed optimizations (parallel downloads, encoding) |
| Phase 11 | 20 min | YouTube Shorts support (9:16 vertical) |
| Phase 12 | 45 min | Portability & Zero-Error Optimization |
| Phase 13 | 30 min | Testing + QA + documentation |

### Critical Path
Environment → RAG → Script Gen → Audio → Video Download → Composition → Upload → CLI → Optimizations → Docs

---

## 2) Project Structure

```
Youtube automation/
├── main.py                      # Entry point — CLI, scheduling, orchestration
├── youtube_automation_agent.py  # Core pipeline — 7 stages (758 lines)
├── rag_engine.py                # RAG engine — ChromaDB + JSON fallback (264 lines)
├── config.json                  # All runtime configuration (21 options)
├── requirements.txt             # Python dependencies (10 packages)
├── setup.bat                    # One-click Windows setup
├── content_calendar.py          # Content scheduling & tracking
├── metrics_tracker.py           # Performance & cost metrics
├── health_check.py              # Pre-run API health checks
├── alerts.py                    # SMTP email alerts
├── logger_config.py             # Rotating file + console logger
├── test_rag.py                  # RAG verification script
├── .env / .env.example          # API keys (gitignored)
├── youtube_credentials.json     # Google OAuth2 credentials
├── rag_data/                    # RAG knowledge base
├── output/                      # Generated videos, audio, thumbnails
└── logs/                        # Rotating log files
```

---

## 3) Phase-by-Phase Build Plan

## Phase 0 — Environment & Scaffold
**Goal:** Get local development environment ready.

### Tasks
- [x] Create project directory and initialize Python virtual environment.
- [x] Install core dependencies: `openai`, `moviepy`, `pillow`, `requests`, `google-auth`, `google-auth-oauthlib`, `google-api-python-client`, `python-dotenv`, `schedule`, `edge-tts`, `chromadb`, `sentence-transformers`.
- [x] Create `.env.example` with all required variables (`GROQ_API_KEY`, `PEXELS_API_KEY`, `YOUTUBE_CREDENTIALS_PATH`).
- [x] Create `setup.bat` for one-click Windows setup.
- [x] Create `logger_config.py` with RotatingFileHandler (10 MB, 5 backups, UTF-8).
- [x] Create `.gitignore` (venv, .env, token.pickle, logs, output, __pycache__).
- [x] **Context7:** Verify MoviePy 2.x import paths and FFmpeg requirements.

### Done Criteria
- Virtual environment activates, all packages install without errors.
- **Bulletproof Setup:** `setup.bat` handles Python/FFmpeg checks and `.env` template creation.

---

## Phase 1 — RAG Engine (Knowledge Retrieval)
**Goal:** Build retrieval-augmented generation system for factual script enhancement.

### Tasks
- [x] Create `rag_engine.py` with `RAGEngine` class.
- [x] Implement ChromaDB vector search backend (`_init_chromadb`, `_retrieve_chromadb`).
- [x] Implement JSON keyword fallback backend (`_init_json_fallback`, `_retrieve_json`).
- [x] Add graceful fallback: try ChromaDB first, fall back to JSON on any error.
- [x] Curate 30+ default facts across domains: space, psychology, ocean, technology, nature, human body.
- [x] Implement `get_context_for_topic(topic, max_facts)` — returns formatted context string for AI prompts.
- [x] Implement `add_knowledge(text, category, tags)` for expanding knowledge base.
- [x] Create `test_rag.py` verification script.
- [x] **Context7:** Verify ChromaDB `get_or_create_collection()` and `query()` API.

### Done Criteria
- `python test_rag.py` returns relevant facts for any topic.
- ChromaDB failure gracefully falls back to JSON search.

---

## Phase 2 — AI Script Generation (Groq LLM)
**Goal:** Generate creative, RAG-enhanced video scripts with structured segment output.

### Tasks
- [x] Create `VideoConfig` dataclass with all 21 configuration options.
- [x] Create `ContentMetadata` dataclass (title, description, tags, hashtags, script, segments).
- [x] Implement `_generate_script_and_metadata(topic)` with multi-model fallback.
- [x] Build deep AI prompt with:
  - RAG fact injection
  - 5 storytelling styles (Narrative, Mystery, Documentary, Discovery, Problem-Solution)
  - Specific video keyword rules (BAD vs GOOD examples)
  - Structured JSON output format with segments + video_keywords
- [x] Implement model fallback chain: Llama 3.3 70B → Llama 3.1 8B → Mixtral 8x7B.
- [x] Add JSON extraction from AI response (regex + strict=False parsing).
- [x] **Context7:** Verify Groq API chat completions (OpenAI-compatible SDK).

### Prompt Template
```text
You are a WORLD-CLASS YouTube scriptwriter who creates VIRAL, MIND-BLOWING content.
CREATE an absolutely CAPTIVATING script about: "{topic}"

📚 KNOWLEDGE BASE (USE THESE FACTS):
{rag_context}

📊 REQUIREMENTS:
• Minimum duration: {video_duration} seconds (~{min_words}+ words)
• Minimum segments: {min_segments}
• Target audience: {target_audience}
• Style: {video_style} | Tone: {tone}

🎯 SCRIPT STRUCTURE:
1. 🪝 HOOK (First 5 seconds) - Something SHOCKING
2. 📖 BODY - Build TENSION, use "But here's the crazy part..." transitions
3. 🎬 CLIMAX - Most mind-blowing revelation
4. 🔔 CALL TO ACTION

🎨 SCRIPT STYLE (CHOOSE ONE): Narrative Journey | Mystery Reveal | Documentary | Discovery | Problem-Solution
❌ AVOID: Always using "X Facts About..." or numbered lists
✅ PREFER: Natural storytelling, intrigue, emotional connection

📤 OUTPUT FORMAT (JSON only):
{
  "title": "Creative clickable title",
  "description": "YouTube description",
  "tags": [...], "hashtags": [...],
  "segments": [
    {"text": "Hook text...", "video_keywords": ["specific visual 1", "specific visual 2"]},
    {"text": "Body text...", "video_keywords": ["relevant visuals"]}
  ]
}
```

### Done Criteria
- Script generates in < 10s with structured JSON segments and video keywords.
- Fallback chain works when primary model is unavailable.

---

## Phase 3 — Audio Generation (Edge-TTS)
**Goal:** Generate human-like narration with configurable voice, rate, and pitch.

### Tasks
- [x] Implement `_generate_audio_robust(script)` using Edge-TTS `Communicate` class.
- [x] Support configurable voice, rate, and pitch from `VideoConfig`.
- [x] Run Edge-TTS asynchronously via `asyncio.run()`.
- [x] Save output as `output/narration.mp3`.
- [x] **Context7:** Verify Edge-TTS `Communicate` constructor and `save()` method.

### Done Criteria
- Clear, natural narration generated in < 15s.
- Voice, rate, and pitch match config.json settings.

---

## Phase 4 — Segment-Matched Video Pipeline (Pexels API)
**Goal:** Download one visually matching clip per script segment.

### Tasks
- [x] Implement `_download_clip_for_segment(keywords, orientation, segment_index)`.
- [x] Search Pexels using each segment's `video_keywords` (not all keywords mixed together).
- [x] Prefer HD quality clips, fallback to any available.
- [x] Support landscape (standard) and portrait (shorts) orientation.
- [x] Parallel download using `ThreadPoolExecutor` with configurable workers.
- [x] **Context7:** Verify Pexels API video search endpoint and response format.

### Algorithm
```
For each segment:
  1. Take segment's video_keywords list
  2. Search Pexels API for first keyword → download first HD result
  3. If fails, try next keyword
  4. If all fail, use previous segment's clip as fallback
  5. Save as segment_{index}_{video_id}.mp4
```

### Done Criteria
- Each segment gets its own matching clip.
- Log shows "Segment X: ✅ Matched clip" for each.

---

## Phase 5 — Video Composition + Background Music
**Goal:** Assemble segment clips, mix audio, and render final video.

### Tasks
- [x] Calculate per-segment duration proportional to word count.
- [x] Cut each clip to match segment speaking duration (trim or loop).
- [x] Resize all clips to target resolution before joining.
- [x] Concatenate using `method="chain"` (3x faster than `compose`).
- [x] Implement `_mix_background_music(narration, duration)` — download from FreePD.com.
- [x] Mix narration + music at configurable volume using `CompositeAudioClip`.
- [x] Render with `libx264`, `ultrafast` preset, 12 threads, `fastdecode` tuning.
- [x] **Context7:** Verify MoviePy 2.x `subclipped()`, `resized()`, `concatenate_videoclips()`, `CompositeAudioClip`.

### Encoding Settings
```python
final_video.write_videofile(
    str(final_video_path),
    fps=config.fps,
    codec="libx264",
    audio_codec="aac",
    preset="ultrafast",
    threads=12,
    ffmpeg_params=["-tune", "fastdecode"]
)
```

### Done Criteria
- Final video renders at target resolution.
- Background music audible but not overpowering narration.
- Video clips match script segment order.

---

## Phase 6 — AI Thumbnail Generation
**Goal:** Auto-generate eye-catching thumbnails from video title.

### Tasks
- [x] Implement `_generate_thumbnail(title)` using Pollinations.ai.
- [x] Build image prompt from title: "YouTube thumbnail, vibrant, eye-catching, {title}".
- [x] Save as `output/thumbnail.jpg`.
- [x] No API key required (Pollinations.ai is free).

### Done Criteria
- Thumbnail image generated and saved.

---

## Phase 7 — YouTube Upload
**Goal:** Automated upload with full metadata and thumbnail.

### Tasks
- [x] Implement `_get_youtube_credentials()` with OAuth2 flow + token.pickle caching.
- [x] Implement `_upload_to_youtube(video_path, metadata, schedule_time)`.
- [x] Set title, description, tags, category (22 = People & Blogs).
- [x] Auto-add `#Shorts` tag and description when format is shorts.
- [x] Implement `_set_thumbnail(youtube, video_id, thumbnail_path)`.
- [x] **Context7:** Verify `MediaFileUpload` and `videos().insert()` API.

### Done Criteria
- Video uploads successfully with all metadata.
- Thumbnail sets on verified channels.

---

## Phase 8 — CLI Interface + Orchestration
**Goal:** Build command-line interface with scheduling support.

### Tasks
- [x] Create `AutomationOrchestrator` class in `main.py`.
- [x] Implement `load_configuration()` — loads config.json + .env.
- [x] Implement `setup_components()` — initializes agent, health monitor, metrics, calendar, alerts.
- [x] Implement `create_single_video(topic, schedule_time)` — full pipeline with error handling.
- [x] Implement `start_scheduler(interval, time_unit)` — periodic runs.
- [x] Add argparse CLI: `--run-once`, `--topic`, `--schedule`.

### CLI Commands
```bash
python main.py --run-once --topic "topic here"
python main.py --schedule "6 hours"
```

### Done Criteria
- CLI works with all flags.
- Orchestrator handles errors gracefully and records metrics.

---

## Phase 9 — Supporting Modules
**Goal:** Add monitoring, tracking, and alerting infrastructure.

### Tasks
- [x] Create `health_check.py` — verify Groq, Pexels, Edge-TTS API availability.
- [x] Create `metrics_tracker.py` — track total videos, successes, failures, costs.
- [x] Create `content_calendar.py` — schedule and track published videos.
- [x] Create `alerts.py` — SMTP email alerts for critical failures.

### Done Criteria
- Health check returns ✅ Online for all APIs.
- Metrics persist across runs in `metrics.json`.

---

## Phase 10 — Speed Optimizations
**Goal:** Make the pipeline as fast as possible at 1080p.

### Tasks
- [x] Parallel video downloads with `ThreadPoolExecutor(max_workers=5)`.
- [x] Switch from `method="compose"` to `method="chain"` (3x faster).
- [x] Increase CPU threads to 12.
- [x] Add `ffmpeg_params=["-tune", "fastdecode"]`.
- [x] Set `preset="ultrafast"`.

### Performance Benchmarks

| Optimization | Impact |
|-------------|--------|
| Parallel downloads | 3x faster downloads |
| Chain concatenation | 3x faster clip joining |
| Ultrafast preset | 2x faster encoding |
| 12 threads | ~50% faster encoding |
| Fastdecode tuning | Additional speed boost |

### Done Criteria
- Total pipeline < 3 minutes for a 90-second video.

---

## Phase 11 — YouTube Shorts Support
**Goal:** Generate vertical videos for YouTube Shorts.

### Tasks
- [x] Support `"format": "shorts"` in config.json.
- [x] Set resolution to 1080×1920 (9:16 vertical).
- [x] Search Pexels with `orientation=portrait`.
- [x] Auto-add `#Shorts` tag to title/description.
- [x] Limit duration to ≤60 seconds.

### Done Criteria
- Shorts videos upload with correct aspect ratio and `#Shorts` tag.

---

## Phase 12 — Testing + QA + Documentation
**Goal:** Verify full pipeline and create documentation.

### Tasks
- [x] Run full pipeline test: `python main.py --run-once --topic "test topic"`.
- [x] Verify output files: `narration.mp3`, `final_video.mp4`, `thumbnail.jpg`.
- [x] Verify YouTube upload succeeds.
- [x] Verify segment-matched clips in logs.
- [x] Verify background music mixing.
- [x] Test RAG engine: `python test_rag.py`.
- [x] Create `README.md` with full documentation.
- [x] Create `BUILD_PLAN.md` (this file).

### Done Criteria
- All tests pass. Documentation complete.

---

## 4) Complete Feature Summary

| # | Feature | Module | Function | Config Key |
|---|---------|--------|----------|------------|
| 1 | AI Script Generation | `youtube_automation_agent.py` | `_generate_script_and_metadata()` | `niche`, `tone`, `video_style` |
| 2 | RAG Knowledge Retrieval | `rag_engine.py` | `get_context_for_topic()` | — |
| 3 | Neural TTS | `youtube_automation_agent.py` | `_generate_audio_robust()` | `voice`, `voice_rate`, `voice_pitch` |
| 4 | Segment-Matched Video | `youtube_automation_agent.py` | `_download_clip_for_segment()` + `_combine_audio_video()` | `parallel_downloads`, `max_download_workers` |
| 5 | Background Music | `youtube_automation_agent.py` | `_mix_background_music()` | `add_music`, `music_volume` |
| 6 | AI Thumbnail | `youtube_automation_agent.py` | `_generate_thumbnail()` | `generate_thumbnail` |
| 7 | YouTube Upload | `youtube_automation_agent.py` | `_upload_to_youtube()` | — |
| 8 | YouTube Shorts | `youtube_automation_agent.py` | Config-driven | `format` |
| 9 | Health Checks | `health_check.py` | `check_api_status()` | — |
| 10 | Metrics Tracking | `metrics_tracker.py` | `record_video()` | — |
| 11 | Content Calendar | `content_calendar.py` | `mark_as_published()` | — |
| 12 | Email Alerts | `alerts.py` | `alert_failure()` | SMTP config |
| 13 | CLI + Scheduling | `main.py` | `main()` + `start_scheduler()` | — |

**Total: 10 Python modules | 758 lines core agent | 21 config options | 3 API integrations | 2 free services**

---

## 5) Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Python | CPython | 3.10–3.13 (3.14+ has ChromaDB/Pydantic issues) |
| AI Model | Groq (Llama 3.3 70B → 3.1 8B → Mixtral 8x7B) | Latest |
| RAG | ChromaDB + Sentence Transformers | ≥0.4.0, ≥2.2.0 |
| TTS | Edge-TTS (Microsoft Neural Voices) | ≥7.2.0 |
| Video | MoviePy 2.x + FFmpeg | ≥2.2.0 |
| Stock Video | Pexels API | Free tier |
| Music | FreePD.com | Free, no API key |
| Thumbnails | Pollinations.ai | Free, no API key |
| Upload | YouTube Data API v3 | Free (10k units/day) |
| Concurrency | concurrent.futures | stdlib |
| Config | python-dotenv + JSON | ≥1.2.0 |

---

## 6) Testing Checklist

### Script Generation
- [x] Script generates with structured JSON segments.
- [x] Each segment has `text` and `video_keywords`.
- [x] RAG facts injected when available.
- [x] Model fallback chain works.
- [x] 5 storytelling styles produce varied output.

### Audio Generation
- [x] Narration audio generated as MP3.
- [x] Voice, rate, and pitch match config.
- [x] Edge-TTS handles long scripts without truncation.

### Video Pipeline
- [x] Each segment gets its own matching clip.
- [x] Clips cut to match segment speaking duration.
- [x] Clips assembled in segment order.
- [x] Fallback clip used when segment search fails.
- [x] Final video renders at target resolution.

### Background Music
- [x] Music downloads from FreePD.com.
- [x] Music mixed at configurable volume.
- [x] Music loops/trims to match video duration.

### Upload & Metadata
- [x] Video uploads to YouTube with correct metadata.
- [x] Shorts mode adds `#Shorts` tag.
- [x] Thumbnail generates and saves.
- [x] Metrics and calendar updated after upload.

### Performance
- [x] Parallel downloads work.
- [x] Chain concatenation used (not compose).
- [x] Encoding uses ultrafast + 12 threads.

---

## 7) Execution Checklist (Master Tracker)

### Core Pipeline
- [x] Environment setup complete
- [x] RAG engine with ChromaDB + JSON fallback
- [x] Script generation with 5 storytelling styles
- [x] Audio generation with Edge-TTS neural voices
- [x] Segment-matched video download pipeline
- [x] Video composition with background music
- [x] AI thumbnail generation
- [x] YouTube upload with full metadata
- [x] CLI interface with scheduling

### Enhancements
- [x] Parallel downloads (ThreadPoolExecutor)
- [x] Speed optimized encoding (ultrafast + 12 threads + chain)
- [x] YouTube Shorts support (9:16 vertical)
- [x] Multiple voice options (10+ Edge-TTS voices)
- [x] Health checks for all APIs
- [x] Metrics tracking
- [x] Content calendar
- [x] Email alerts
- [x] **Bulletproof portability & Zero-error run**
- [x] **Multi-source background music & thumbnail fallbacks**

### Documentation
- [x] README.md with full project documentation
- [x] BUILD_PLAN.md with phase-by-phase guide
- [x] .env.example with all required variables
- [x] config.json with sensible defaults

### Future Enhancements
- [ ] Auto subtitles (word-level timestamps + on-screen rendering)
- [ ] Music fade in/out effects
- [ ] Multi-language support
- [ ] Analytics dashboard
- [ ] A/B thumbnail testing
- [ ] Scheduled YouTube publishing

---

## Notes
- Keep scope strict to implemented features.
- Always use **Context7** before modifying or adding any library dependency.
- If blocked on optional features, prioritize core pipeline and deployment first.
- All API errors are handled gracefully with fallbacks and logging.
