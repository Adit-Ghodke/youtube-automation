"""
Core component for the YouTube Automation Agent.
Handles the entire video creation pipeline from script to upload.
"""
import os
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
import logging
import time
import shutil
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- FINAL FIX for Pillow/MoviePy Compatibility ---
from PIL import Image as PILImage
if not hasattr(PILImage, 'ANTIALIAS'):
    PILImage.ANTIALIAS = PILImage.Resampling.LANCZOS
# --- END OF FINAL FIX ---

# Core dependencies
from openai import OpenAI
import edge_tts
import asyncio
from moviepy import *
import requests

# RAG (Retrieval-Augmented Generation)
from rag_engine import RAGEngine

# Google API for YouTube upload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class VideoConfig:
    """Configuration for video style and content."""
    niche: str
    target_audience: str
    video_style: str
    tone: str
    language: str
    video_duration: int
    fps: int
    # Video format
    format: str = "standard"  # "standard" or "shorts"
    resolution: str = "1080p"  # "1080p" or "720p"
    # Voice settings
    voice: str = "en-US-AriaNeural"
    voice_rate: str = "+0%"
    voice_pitch: str = "+0Hz"
    # Feature toggles
    add_subtitles: bool = True
    subtitle_style: str = "modern"
    add_music: bool = True
    music_volume: float = 0.15
    generate_thumbnail: bool = True
    # Performance
    parallel_downloads: bool = True
    max_download_workers: int = 5

@dataclass
class ContentMetadata:
    """Holds the generated metadata for the video."""
    title: str
    description: str
    tags: list
    hashtags: list
    script: str
    segments: list  # List of {"text": "...", "video_keywords": ["..."]}


class VideoAutomationAgent:
    """The main agent that orchestrates the video creation process."""

    def __init__(self,
                 groq_key: str,
                 pexels_key: str,
                 youtube_credentials: str,
                 config: VideoConfig,
                 output_dir: str = "output"):

        self.pexels_key = pexels_key
        self.youtube_credentials = youtube_credentials
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Initialize Groq client (OpenAI-compatible API)
        self.groq_client = OpenAI(
            api_key=groq_key,
            base_url="https://api.groq.com/openai/v1"
        )
        
        # Initialize RAG engine for enhanced script generation
        self.rag_engine = RAGEngine(persist_directory="./rag_data")
        logger.info(f"RAG Engine: {self.rag_engine.get_stats()}")

    def _cleanup_output_directory(self):
        """Deletes all files in the output directory to ensure a clean run."""
        logger.info("Cleaning up output directory for a fresh start...")
        if self.output_dir.exists():
            for item in self.output_dir.iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                except Exception as e:
                    # This is just a warning, we don't want to stop the script
                    logger.warning(f"Could not remove item {item.name}: {e}. Continuing...")

    def create_and_publish_video(self, topic: str = None, schedule_time: datetime = None) -> dict:
        """Main method to run the full video creation and publishing pipeline."""
        self._cleanup_output_directory()
        try:
            logger.info("Starting the video creation pipeline...")

            metadata = self._generate_script_and_metadata(topic)
            audio_path = self._generate_audio_robust(metadata.script)
            final_video_path = self._combine_audio_video(metadata, audio_path)
            video_url = self._upload_to_youtube(final_video_path, metadata, schedule_time)

            logger.info(f"Pipeline complete. Video URL: {video_url}")
            return {
                "success": True,
                "url": video_url,
                "metadata": metadata.__dict__,
                "cost": 0.0
            }
        except Exception as e:
            logger.error(f"An error occurred in the pipeline: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _get_youtube_credentials(self) -> Credentials:
        """Handles YouTube API authentication."""
        creds = None
        token_path = Path('token.pickle')
        creds_path = Path(self.youtube_credentials)

        if not creds_path.exists():
            raise FileNotFoundError(
                f"YouTube credentials file not found at '{creds_path}'. "
                "Please run the authentication process."
            )

        if token_path.exists():
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"Failed to refresh token ({e}). Deleting token and re-authenticating.")
                    if token_path.exists():
                        token_path.unlink() 
                    creds = None 
            
            if not creds or not creds.valid:
                flow = InstalledAppFlow.from_client_secrets_file(
                    creds_path,
                    scopes=['https://www.googleapis.com/auth/youtube.upload'] 
                )
                creds = flow.run_local_server(port=0)
            
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        return creds

    def _generate_script_and_metadata(self, topic: str) -> ContentMetadata:
        """Generates script and metadata using Groq AI with RAG-enhanced context."""
        logger.info(f"Generating script for topic: {topic or 'trending topic'}...")
        
        # Calculate minimum words for the target duration (approx 150 words per minute)
        min_words = int(self.config.video_duration * 2.5)  # ~150 words/min
        min_segments = max(8, self.config.video_duration // 10)  # At least 1 segment per 10 seconds
        
        # === RAG: Retrieve relevant facts ===
        rag_context = ""
        if self.rag_engine.enabled:
            rag_context = self.rag_engine.get_context_for_topic(topic or self.config.niche, max_facts=7)
            if rag_context:
                logger.info(f"RAG retrieved context for topic: {topic}")
        
        prompt = f"""
You are a WORLD-CLASS YouTube scriptwriter who creates VIRAL, MIND-BLOWING content.

CREATE an absolutely CAPTIVATING script about: "{topic or self.config.niche}"

{f'''═══════════════════════════════════════════════════════════
📚 KNOWLEDGE BASE (USE THESE FACTS IN YOUR SCRIPT):
═══════════════════════════════════════════════════════════
{rag_context}

IMPORTANT: Incorporate at least 3-4 of these facts naturally into your script!
''' if rag_context else ''}
═══════════════════════════════════════════════════════════
📊 REQUIREMENTS:
═══════════════════════════════════════════════════════════
• Minimum duration: {self.config.video_duration} seconds (about {min_words}+ words)
• Minimum segments: {min_segments} segments
• Target audience: {self.config.target_audience}
• Style: {self.config.video_style}
• Tone: {self.config.tone}

═══════════════════════════════════════════════════════════
🎯 SCRIPT STRUCTURE (MUST FOLLOW):
═══════════════════════════════════════════════════════════

1. 🪝 HOOK (First 5 seconds) - Start with something SHOCKING:
   - "What if I told you..." 
   - "In the next 60 seconds, your mind will be BLOWN..."
   - A surprising statistic or fact
   - A provocative question

2. 📖 BODY - Use these storytelling techniques:
   - Build TENSION and SUSPENSE
   - Use "But here's the crazy part..." transitions
   - Include specific numbers, dates, and facts
   - Make comparisons people can visualize
   - Add "plot twists" and reveals

3. 🎬 CLIMAX - The most mind-blowing revelation

4. 🔔 CALL TO ACTION - "Subscribe for more..." or similar

═══════════════════════════════════════════════════════════
🎬 VIDEO KEYWORDS RULES (CRITICAL):
═══════════════════════════════════════════════════════════
Each segment MUST have SPECIFIC, SEARCHABLE video keywords.

❌ BAD keywords: ["space", "science", "nature"]
✅ GOOD keywords: ["astronaut floating space station", "supernova explosion", "earth from space"]

Be SPECIFIC - describe exactly what should appear on screen!

═══════════════════════════════════════════════════════════
🎨 SCRIPT STYLE (CHOOSE ONE - BE CREATIVE):
═══════════════════════════════════════════════════════════

Pick ONE of these engaging formats (VARY your choice each time!):

1. 🌟 NARRATIVE JOURNEY - Tell a story with a beginning, middle, and end
   Example: "Imagine you're standing at the edge of the deepest ocean..."

2. 🔍 MYSTERY REVEAL - Build suspense and reveal surprising truths
   Example: "Scientists have discovered something that will change everything..."

3. 🎬 DOCUMENTARY STYLE - Explore the topic deeply and thoughtfully
   Example: "In the depths of space, something extraordinary is happening..."

4. 💡 DISCOVERY FORMAT - Take viewers on a journey of learning
   Example: "What if I told you that everything you know about X is wrong?"

5. 🎯 PROBLEM-SOLUTION - Present a challenge and reveal the answer
   Example: "The biggest question in science has finally been answered..."

❌ AVOID: Always using "X Facts About..." or numbered lists
✅ PREFER: Natural storytelling, building intrigue, emotional connection

═══════════════════════════════════════════════════════════
🎬 VIDEO KEYWORDS RULES (CRITICAL):
═══════════════════════════════════════════════════════════
Each segment MUST have SPECIFIC, SEARCHABLE video keywords.

❌ BAD keywords: ["space", "science", "nature"]
✅ GOOD keywords: ["astronaut floating space station", "supernova explosion", "earth from space"]

Be SPECIFIC - describe exactly what should appear on screen!

═══════════════════════════════════════════════════════════
📤 OUTPUT FORMAT (JSON only):
═══════════════════════════════════════════════════════════
Return ONLY a JSON object with:
{{
  "title": "Creative, clickable title (avoid numbered lists when possible)",
  "description": "Detailed YouTube description",
  "tags": ["tag1", "tag2", ...],
  "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"],
  "segments": [
    {{
      "text": "Your captivating hook - make viewers want to stay!",
      "video_keywords": ["specific visual 1", "specific visual 2"]
    }},
    {{
      "text": "Fact number one: [fact content]...",
      "video_keywords": ["relevant visuals"]
    }},
    // Continue with numbered facts if title has a number
  ]
}}

RESPOND WITH ONLY THE JSON. NO OTHER TEXT."""
        
        
        # Groq models to try (in order of preference)
        # See available models at: https://console.groq.com/docs/models
        models_to_try = [
            "llama-3.3-70b-versatile",  # Best quality, free tier
            "llama-3.1-8b-instant",      # Faster fallback
            "gemma2-9b-it",              # Alternative
        ]
        
        last_error = None
        for model in models_to_try:
            try:
                logger.info(f"Trying Groq model: {model}")
                response = self.groq_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=2048
                )
                
                # Check if response is valid
                if not response or not response.choices:
                    logger.warning(f"Model {model} returned empty response, trying next...")
                    continue
                    
                raw_content = response.choices[0].message.content
                if not raw_content:
                    logger.warning(f"Model {model} returned empty content, trying next...")
                    continue
                
                logger.info(f"Successfully got response from {model}")
                break
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}")
                last_error = e
                continue
        else:
            raise Exception(f"All Groq models failed. Last error: {last_error}")
        
        # Extract JSON from response (model may include extra text)
        json_match = re.search(r'\{[\s\S]*\}', raw_content)
        if not json_match:
            raise ValueError(f"Could not extract JSON from AI response: {raw_content[:200]}")
        
        # Clean the JSON string - remove invalid control characters
        json_str = json_match.group()
        # Replace problematic control chars that break JSON parsing
        json_str = re.sub(r'[\x00-\x1f\x7f]', lambda m: ' ' if m.group() in '\n\r\t' else '', json_str)
        
        try:
            content = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}. Trying with strict=False...")
            # Try parsing with more lenient approach
            content = json.loads(json_str, strict=False)

        # Extract segments with video keywords
        segments = content.get('segments', [])
        
        # Build full script from segments
        if segments:
            final_script = " ".join(seg.get('text', '') for seg in segments)
            logger.info(f"Extracted {len(segments)} segments with video keywords")
        else:
            # Fallback to old script format if segments not provided
            script_data = content.get('script', '')
            if isinstance(script_data, dict):
                final_script = "\n\n".join(str(part) for part in script_data.values())
            elif isinstance(script_data, list):
                final_script = "\n\n".join(str(item) for item in script_data)
            else:
                final_script = str(script_data)
            # Create simple segments from script for backwards compatibility
            sentences = re.split(r'(?<=[.!?])\s+', final_script)
            segments = [{"text": s, "video_keywords": content.get('tags', [])[:3]} for s in sentences if s.strip()]
        
        if not final_script:
            raise ValueError("AI failed to generate a valid script.")

        return ContentMetadata(
            title=content.get('title', 'AI Generated Video'),
            description=content.get('description', 'No description provided.'),
            tags=content.get('tags', []),
            hashtags=content.get('hashtags', []),
            script=final_script,
            segments=segments
        )

    def _generate_audio_robust(self, script: str) -> str:
        """
        Generates audio using Edge-TTS (Microsoft neural voices) for natural-sounding speech.
        Supports configurable voice, rate, and pitch.
        """
        logger.info("Generating audio with Edge-TTS (Microsoft neural voice)...")
        final_audio_path = self.output_dir / "narration.mp3"
        
        # Use voice from config
        voice = getattr(self.config, 'voice', 'en-US-AriaNeural')
        rate = getattr(self.config, 'voice_rate', '+0%')
        pitch = getattr(self.config, 'voice_pitch', '+0Hz')
        
        logger.info(f"Voice: {voice}, Rate: {rate}, Pitch: {pitch}")
        
        async def generate_audio():
            communicate = edge_tts.Communicate(script, voice, rate=rate, pitch=pitch)
            await communicate.save(str(final_audio_path))
        
        # Run async function
        asyncio.run(generate_audio())
        
        logger.info(f"Audio generated successfully with voice: {voice}")
        return str(final_audio_path)

    def _download_clip_for_segment(self, keywords: list, orientation: str, segment_index: int) -> str:
        """Downloads ONE best video clip for a specific segment's keywords."""
        headers = {"Authorization": self.pexels_key}
        
        for keyword in keywords:
            try:
                url = f"https://api.pexels.com/videos/search?query={keyword}&per_page=3&orientation={orientation}"
                res = requests.get(url, headers=headers, timeout=20)
                res.raise_for_status()
                videos = res.json().get('videos', [])
                
                for video in videos:
                    video_files = video.get('video_files', [])
                    # Prefer HD quality
                    link = next((f['link'] for f in video_files if f.get('quality') == 'hd'), None)
                    if not link:
                        link = next((f['link'] for f in video_files if f.get('link')), None)
                    
                    if link:
                        clip_path = self.output_dir / f"segment_{segment_index}_{video['id']}.mp4"
                        response = requests.get(link, timeout=60)
                        response.raise_for_status()
                        with open(clip_path, 'wb') as f:
                            f.write(response.content)
                        logger.info(f"  Segment {segment_index}: Downloaded clip for '{keyword}'")
                        return str(clip_path)
                        
            except Exception as e:
                logger.warning(f"  Segment {segment_index}: Failed to find clip for '{keyword}': {e}")
                continue
        
        return None

    def _combine_audio_video(self, metadata: ContentMetadata, audio_path: str) -> str:
        """Downloads segment-matched clips and combines with audio and music."""
        logger.info("=== SEGMENT-MATCHED VIDEO ASSEMBLY ===")
        audio_clip = AudioFileClip(audio_path)
        video_duration = audio_clip.duration
        
        # Determine resolution
        resolution_map = {
            "1080p": (1920, 1080),
            "720p": (1280, 720),
        }
        is_shorts = getattr(self.config, 'format', 'standard') == "shorts"
        if is_shorts:
            resolution = (1080, 1920)
        else:
            resolution = resolution_map.get(getattr(self.config, 'resolution', '1080p'), (1920, 1080))
        
        orientation = "portrait" if is_shorts else "landscape"
        logger.info(f"Target resolution: {resolution}, Shorts mode: {is_shorts}")
        
        segments = metadata.segments
        if not segments:
            raise Exception("No segments found in metadata!")
        
        # === STEP 1: Calculate each segment's duration based on word count ===
        total_words = sum(len(seg.get('text', '').split()) for seg in segments)
        segment_durations = []
        for seg in segments:
            word_count = len(seg.get('text', '').split())
            # Duration proportional to word count
            seg_duration = (word_count / max(total_words, 1)) * video_duration
            seg_duration = max(seg_duration, 1.0)  # At least 1 second per segment
            segment_durations.append(seg_duration)
        
        # Normalize so total matches video duration
        duration_sum = sum(segment_durations)
        segment_durations = [(d / duration_sum) * video_duration for d in segment_durations]
        
        logger.info(f"Processing {len(segments)} segments (total duration: {video_duration:.1f}s)")
        for i, (seg, dur) in enumerate(zip(segments, segment_durations)):
            keywords = seg.get('video_keywords', [])
            logger.info(f"  Segment {i+1}: {dur:.1f}s | Keywords: {keywords[:3]}")
        
        # === STEP 2: Download clips per segment (parallel) ===
        clip_paths = []
        max_workers = getattr(self.config, 'max_download_workers', 5)
        
        def download_for_segment(args):
            idx, seg = args
            keywords = seg.get('video_keywords', [])
            if not keywords:
                # Extract keywords from text as fallback
                text = seg.get('text', '')
                keywords = [word for word in text.split() if len(word) > 4][:3]
            return idx, self._download_clip_for_segment(keywords, orientation, idx)
        
        logger.info(f"Downloading clips for {len(segments)} segments with {max_workers} workers...")
        
        segment_clips = [None] * len(segments)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(download_for_segment, (i, seg)) for i, seg in enumerate(segments)]
            for future in as_completed(futures):
                idx, path = future.result()
                segment_clips[idx] = path
                if path:
                    clip_paths.append(path)
        
        # === STEP 3: Build video clips matched to segments ===
        final_clips = []
        
        # Keep a fallback clip in case a segment has no match
        fallback_clip = None
        
        for i, (clip_path, target_duration) in enumerate(zip(segment_clips, segment_durations)):
            if clip_path:
                try:
                    clip = VideoFileClip(clip_path)
                    fallback_clip = clip_path  # Update fallback
                    
                    # Cut clip to match segment duration
                    if clip.duration > target_duration:
                        clip = clip.subclipped(0, target_duration)
                    elif clip.duration < target_duration:
                        # Loop the clip to fill the duration
                        loops = int(target_duration / clip.duration) + 1
                        clips_looped = [clip] * loops
                        clip = concatenate_videoclips(clips_looped, method="chain")
                        clip = clip.subclipped(0, target_duration)
                    
                    clip = clip.resized(resolution)
                    final_clips.append(clip)
                    logger.info(f"  Segment {i+1}: ✅ Matched clip ({target_duration:.1f}s)")
                    continue
                except Exception as e:
                    logger.warning(f"  Segment {i+1}: Error loading clip: {e}")
            
            # Fallback: use previous clip or a generic search
            if fallback_clip:
                try:
                    clip = VideoFileClip(fallback_clip)
                    if clip.duration > target_duration:
                        clip = clip.subclipped(0, target_duration)
                    clip = clip.resized(resolution)
                    final_clips.append(clip)
                    logger.info(f"  Segment {i+1}: ⚠️ Used fallback clip ({target_duration:.1f}s)")
                except Exception as e:
                    logger.warning(f"  Segment {i+1}: Fallback also failed: {e}")
        
        if not final_clips:
            raise Exception("Could not create any video clips for segments!")
        
        # === STEP 4: Concatenate in order ===
        logger.info(f"Assembling {len(final_clips)} matched clips...")
        final_clip = concatenate_videoclips(final_clips, method="chain")
        final_clip = final_clip.with_duration(video_duration)
        
        # Mix audio with background music if enabled
        if getattr(self.config, 'add_music', True):
            try:
                final_audio = self._mix_background_music(audio_clip, video_duration)
            except Exception as e:
                logger.info(f"Background music skipped, using narration only")
                final_audio = audio_clip
        else:
            final_audio = audio_clip
        
        final_video = final_clip.with_audio(final_audio)
        final_video_path = self.output_dir / "final_video.mp4"
        
        final_video.write_videofile(
            str(final_video_path), 
            fps=self.config.fps, 
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=12,
            ffmpeg_params=["-tune", "fastdecode"]
        )
        
        # Close ALL clips properly before cleanup
        try:
            audio_clip.close()
        except:
            pass
        try:
            final_clip.close()
        except:
            pass
        try:
            final_video.close()
        except:
            pass
        for clip in final_clips:
            try:
                clip.close()
            except:
                pass
        
        # Small delay to let Windows release file handles
        import time
        time.sleep(1)
        
        for path in clip_paths:
            try:
                os.remove(path)
            except:
                pass  # Silently ignore — temp files will be cleaned on next run

        return str(final_video_path)
    
    def _mix_background_music(self, narration: AudioFileClip, duration: float) -> AudioFileClip:
        """Downloads royalty-free music and mixes it with narration."""
        from moviepy import CompositeAudioClip
        
        logger.info("Adding background music...")
        music_volume = getattr(self.config, 'music_volume', 0.15)
        music_path = self.output_dir / "background_music.mp3"
        
        # List of royalty-free music URLs (multiple sources for reliability)
        music_urls = [
            "https://cdn.pixabay.com/audio/2024/11/29/audio_a0b0d771d4.mp3",
            "https://cdn.pixabay.com/audio/2024/09/10/audio_6e4bbc1c33.mp3",
            "https://cdn.pixabay.com/audio/2022/02/23/audio_d1718ab41b.mp3",
            "https://www.freepd.com/music/Chill%20Abstract%20Intention.mp3",
            "https://www.freepd.com/music/Deep%20Haze.mp3",
        ]
        
        # Browser headers to avoid 403 blocks
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        try:
            # Try to download background music
            for url in music_urls:
                try:
                    response = requests.get(url, timeout=30, headers=headers)
                    if response.status_code == 200 and len(response.content) > 10000:
                        with open(music_path, 'wb') as f:
                            f.write(response.content)
                        logger.info(f"Downloaded background music successfully")
                        break
                except Exception:
                    continue
            
            if not music_path.exists():
                logger.info("Background music sources unavailable, proceeding with narration only")
                return narration
            
            # Load and process background music
            music_clip = AudioFileClip(str(music_path))
            
            # Loop music to match video duration
            if music_clip.duration < duration:
                loops_needed = int(duration / music_clip.duration) + 1
                music_clips = [music_clip] * loops_needed
                music_clip = concatenate_audioclips(music_clips)
            
            # Trim to match duration
            music_clip = music_clip.subclipped(0, duration)
            
            # Reduce music volume
            music_clip = music_clip.with_volume_scaled(music_volume)
            
            # Composite narration (full volume) with music (lowered)
            final_audio = CompositeAudioClip([narration, music_clip])
            
            logger.info(f"Background music mixed at {music_volume*100}% volume")
            return final_audio
            
        except Exception as e:
            logger.info(f"Background music mixing skipped, using narration only")
            return narration

    def _upload_to_youtube(self, video_path: str, metadata: ContentMetadata, schedule_time: datetime = None):
        """Uploads the final video to YouTube."""
        logger.info("Authenticating and uploading to YouTube...")
        credentials = self._get_youtube_credentials()
        youtube = build('youtube', 'v3', credentials=credentials)
        
        # Add #Shorts tag if in shorts mode
        is_shorts = getattr(self.config, 'format', 'standard') == "shorts"
        tags = metadata.tags.copy() if metadata.tags else []
        description = metadata.description
        
        if is_shorts:
            if "#Shorts" not in tags:
                tags.insert(0, "#Shorts")
            if "#shorts" not in description.lower():
                description = "#Shorts\n\n" + description
            logger.info("Added #Shorts tag for YouTube Shorts")
        
        body = {
            'snippet': {
                'title': metadata.title,
                'description': description,
                'tags': tags,
                'categoryId': '28' 
            },
            'status': {
                'privacyStatus': 'private', 
                'selfDeclaredMadeForKids': False
            }
        }
        if schedule_time:
            body['status']['publishAt'] = schedule_time.isoformat() + "Z"

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

        request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"Uploaded {int(status.progress() * 100)}%.")
        
        video_id = response.get('id')
        logger.info(f"Video uploaded successfully! Video ID: {video_id}")
        
        # Generate and upload thumbnail if enabled
        if getattr(self.config, 'generate_thumbnail', True):
            try:
                thumbnail_path = self._generate_thumbnail(metadata.title)
                if thumbnail_path:
                    self._set_thumbnail(youtube, video_id, thumbnail_path)
            except Exception as e:
                logger.warning(f"Could not set thumbnail: {e}")
        
        return f"https://www.youtube.com/watch?v={video_id}"
    
    def _generate_thumbnail(self, title: str) -> str:
        """Generate an eye-catching thumbnail using Pollinations.ai with retry and fallback."""
        logger.info("Generating AI thumbnail...")
        import urllib.parse
        
        thumbnail_path = self.output_dir / "thumbnail.jpg"
        
        # Try multiple prompt variations (shorter prompts are more reliable)
        prompts = [
            f"youtube thumbnail vibrant {title[:50]}",
            f"colorful digital art {title[:30]}",
            f"eye catching thumbnail {title.split()[0] if title else 'science'}",
        ]
        
        for prompt in prompts:
            try:
                encoded_prompt = urllib.parse.quote(prompt)
                url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true"
                response = requests.get(url, timeout=90)
                if response.status_code == 200 and len(response.content) > 5000:
                    with open(thumbnail_path, 'wb') as f:
                        f.write(response.content)
                    logger.info(f"Thumbnail generated successfully")
                    return str(thumbnail_path)
            except Exception:
                continue
        
        # Fallback: download a relevant stock image from Pexels as thumbnail
        try:
            search_term = title.split()[0] if title else "science"
            pexels_url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(search_term)}&per_page=1&orientation=landscape"
            headers = {"Authorization": self.pexels_key}
            response = requests.get(pexels_url, timeout=15, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data.get("photos"):
                    img_url = data["photos"][0]["src"]["landscape"]
                    img_response = requests.get(img_url, timeout=15)
                    if img_response.status_code == 200:
                        with open(thumbnail_path, 'wb') as f:
                            f.write(img_response.content)
                        logger.info("Thumbnail generated from Pexels fallback")
                        return str(thumbnail_path)
        except Exception:
            pass
        
        logger.info("Thumbnail generation skipped — video uploaded without custom thumbnail")
        return None
    
    def _set_thumbnail(self, youtube, video_id: str, thumbnail_path: str):
        """Upload thumbnail to YouTube video."""
        logger.info(f"Uploading thumbnail to video {video_id}...")
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
            logger.info("Thumbnail uploaded successfully!")
        except Exception as e:
            logger.warning(f"Thumbnail upload failed (may require verified channel): {e}")
