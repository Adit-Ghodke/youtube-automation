import json
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ContentCalendar:
    """Manages the schedule of video content."""

    def __init__(self, calendar_file: str = "content_calendar.json"):
        self.calendar_file = Path(calendar_file)
        self.load_calendar()

    def load_calendar(self):
        """Loads the calendar from a JSON file."""
        if self.calendar_file.exists():
            try:
                with open(self.calendar_file) as f:
                    self.calendar = json.load(f)
            except json.JSONDecodeError:
                logger.warning("Content calendar file is corrupted. Starting new calendar.")
                self._initialize_calendar()
        else:
            self._initialize_calendar()

    def _initialize_calendar(self):
        """Creates a new, empty calendar structure."""
        self.calendar = {"scheduled_videos": [], "published_videos": []}

    def save_calendar(self):
        """Saves the current calendar state to the JSON file."""
        try:
            with open(self.calendar_file, 'w') as f:
                json.dump(self.calendar, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save content calendar: {e}")

    def add_video(self, metadata: dict, publish_time: datetime):
        """Adds a new video to the scheduled list."""
        self.calendar["scheduled_videos"].append({
            "topic": metadata.get("title", "N/A"),
            "publish_time": publish_time.isoformat() if publish_time else "manual",
            "status": "scheduled"
        })
        self.save_calendar()
        logger.info(f"Scheduled video: {metadata.get('title', 'N/A')}")

    def mark_as_published(self, video_url: str, metadata: dict):
        """Moves a video from scheduled to published."""
        topic_to_find = metadata.get("title", "N/A")
        
        # Find and remove from scheduled list
        scheduled_video = None
        for video in self.calendar["scheduled_videos"]:
            if video["topic"] == topic_to_find:
                scheduled_video = video
                break
        
        if scheduled_video:
            self.calendar["scheduled_videos"].remove(scheduled_video)

        # Add to published list
        self.calendar["published_videos"].append({
            "topic": topic_to_find,
            "published_at": datetime.now().isoformat(),
            "url": video_url,
            "status": "published"
        })
        self.save_calendar()
        logger.info(f"Marked as published: {topic_to_find}")
