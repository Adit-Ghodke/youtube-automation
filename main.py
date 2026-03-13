"""
Main Execution Script for YouTube AI Video Automation
Includes CLI interface, scheduling, and monitoring
"""

import argparse
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
import json
import schedule
import time
from dotenv import load_dotenv

# Import automation components
from youtube_automation_agent import (
    VideoAutomationAgent,
    VideoConfig,
    ContentMetadata
)

# Import monitoring components
from logger_config import setup_logger
from metrics_tracker import MetricsTracker
from health_check import HealthMonitor
from alerts import AlertSystem
from content_calendar import ContentCalendar

# Load environment variables
load_dotenv()

# Setup logger
logger = setup_logger('main', 'automation.log')


class AutomationOrchestrator:
    """Enhanced orchestrator with monitoring and error handling"""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.load_configuration()
        self.setup_components()

    def load_configuration(self):
        """Load configuration from file or environment"""
        if os.path.exists(self.config_file):
            with open(self.config_file) as f:
                config_data = json.load(f)
        else:
            # Create default configuration if not exists
            config_data = {
                "niche": "educational facts and science",
                "target_audience": "tech enthusiasts",
                "video_style": "educational",
                "tone": "professional yet friendly",
                "language": "en",
                "video_duration": 180,
                "fps": 30,
                "format": "standard",
                "resolution": "1080p",
                "voice": "en-US-AriaNeural",
                "voice_rate": "+0%",
                "voice_pitch": "+0Hz",
                "add_subtitles": True,
                "add_music": True,
                "generate_thumbnail": True,
                "parallel_downloads": True,
                "max_download_workers": 5
            }
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)

        # Create VideoConfig with new structure (with defaults for missing fields)
        self.config = VideoConfig(
            niche=config_data.get("niche", "technology tutorials"),
            target_audience=config_data.get("target_audience", "tech enthusiasts"),
            video_style=config_data.get("video_style", "educational"),
            tone=config_data.get("tone", "professional"),
            language=config_data.get("language", "en"),
            video_duration=config_data.get("video_duration", 90),
            fps=config_data.get("fps", 30),
            format=config_data.get("format", "standard"),
            resolution=config_data.get("resolution", "1080p"),
            voice=config_data.get("voice", "en-US-AriaNeural"),
            voice_rate=config_data.get("voice_rate", "+0%"),
            voice_pitch=config_data.get("voice_pitch", "+0Hz"),
            add_subtitles=config_data.get("add_subtitles", True),
            subtitle_style=config_data.get("subtitle_style", "modern"),
            add_music=config_data.get("add_music", True),
            music_volume=config_data.get("music_volume", 0.15),
            generate_thumbnail=config_data.get("generate_thumbnail", True),
            parallel_downloads=config_data.get("parallel_downloads", True),
            max_download_workers=config_data.get("max_download_workers", 5)
        )
        logger.info(f"Configuration loaded for niche: {config_data.get('niche')}")

    def setup_components(self):
        """Initialize all system components"""
        logger.info("Initializing system components...")

        # API Keys
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.pexels_key = os.getenv("PEXELS_API_KEY")
        self.youtube_creds = os.getenv("YOUTUBE_CREDENTIALS_PATH", "youtube_credentials.json")

        # Check if .env exists
        if not os.path.exists(".env"):
            logger.error("Missing .env file! Run setup.bat or copy .env.example to .env")
            logger.error("Then edit .env and add your API keys.")
            print("\n❌ ERROR: .env file not found!")
            print("   Run setup.bat first, or: copy .env.example .env")
            print("   Then edit .env with your actual API keys.\n")
            sys.exit(1)

        # Validate required API keys (check for missing or placeholder values)
        placeholder_values = ["your-groq-api-key-here", "your-pexels-api-key-here", "", None]
        
        missing_keys = []
        if self.groq_key in placeholder_values:
            missing_keys.append("GROQ_API_KEY    → Get free key: https://console.groq.com/keys")
        if self.pexels_key in placeholder_values:
            missing_keys.append("PEXELS_API_KEY  → Get free key: https://www.pexels.com/api/")
        
        if missing_keys:
            print("\n❌ ERROR: Missing API keys in .env file!")
            print("   Edit the .env file and add these keys:\n")
            for key in missing_keys:
                print(f"   • {key}")
            print()
            sys.exit(1)

        # Initialize automation agent with Groq API
        self.agent = VideoAutomationAgent(
            groq_key=self.groq_key,
            pexels_key=self.pexels_key,
            youtube_credentials=self.youtube_creds,
            config=self.config,
            output_dir="./output"
        )

        # Initialize monitoring
        self.metrics = MetricsTracker("metrics.json")
        self.health = HealthMonitor()
        self.calendar = ContentCalendar("content_calendar.json")

        # Initialize alerts (optional)
        alert_config = {
            "host": os.getenv("SMTP_HOST"),
            "port": int(os.getenv("SMTP_PORT", 587)),
            "email": os.getenv("ALERT_EMAIL"),
            "password": os.getenv("ALERT_PASSWORD"),
            "recipient": os.getenv("ALERT_RECIPIENT")
        }

        if alert_config["email"]:
            self.alerts = AlertSystem(alert_config)
        else:
            self.alerts = None

        logger.info("All components initialized successfully")

    def create_single_video(self, topic: str = None, schedule_time: datetime = None):
        """Create and publish a single video"""
        logger.info("=" * 50)
        logger.info(f"Starting video creation process for topic: '{topic or 'auto-generated'}'")
        logger.info("=" * 50)

        start_time = datetime.now()
        video_data = {"topic": topic, "success": False}

        try:
            # Run health check
            health_status = self.health.check_api_status()
            logger.info(f"API Health: {health_status}")

            # Check for offline APIs
            offline_apis = [api for api, status in health_status.items() if "Offline" in status]
            if offline_apis:
                raise Exception(f"APIs offline: {', '.join(offline_apis)}")

            # Create video
            result = self.agent.create_and_publish_video(
                topic=topic,
                schedule_time=schedule_time
            )

            if not result.get("success"):
                raise Exception(result.get("error", "Unknown error in video creation agent."))

            # If successful
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Successfully created and published video. Duration: {duration:.2f} seconds.")
            logger.info(f"Video URL: {result.get('url')}")

            # Record metrics
            video_data.update({
                "success": True,
                "duration": duration,
                "video_id": result.get("url", "").split('/')[-1],
                "api_cost": result.get("cost", 0)
            })
            self.metrics.record_video(video_data)
            self.calendar.mark_as_published(result.get("url"), result.get("metadata", {}))

        except Exception as e:
            logger.error(f"❌ Video creation failed: {e}", exc_info=True)
            duration = (datetime.now() - start_time).total_seconds()
            video_data["duration"] = duration
            self.metrics.record_video(video_data)
            if self.alerts:
                self.alerts.alert_failure(str(e))

    def start_scheduler(self, interval: int, time_unit: str):
        """Start the scheduler to run the job periodically."""
        logger.info(f"Scheduler started. Will run every {interval} {time_unit}.")
        job = self.create_single_video
        
        if time_unit == 'hours':
            schedule.every(interval).hours.do(job)
        elif time_unit == 'days':
            schedule.every(interval).days.do(job)
        elif time_unit == 'minutes':
            schedule.every(interval).minutes.do(job)
        
        # Run the job once immediately
        self.create_single_video()

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("🛑 Scheduler stopped by user.")


def main():
    """Main function to handle command-line arguments."""
    parser = argparse.ArgumentParser(description="YouTube AI Video Automation")
    parser.add_argument("--run-once", action="store_true", help="Run the video creation process once.")
    parser.add_argument("--topic", type=str, help="Specify a topic for the video.")
    parser.add_argument("--schedule", type=str, help="Schedule the job (e.g., '1 day', '12 hours').")

    args = parser.parse_args()
    orchestrator = AutomationOrchestrator()

    if args.run_once:
        orchestrator.create_single_video(topic=args.topic)
    elif args.schedule:
        try:
            interval, unit = args.schedule.split()
            unit = unit.lower()
            if not unit.endswith('s'):
                unit += 's'
            orchestrator.start_scheduler(int(interval), unit)
        except ValueError:
            logger.error("Invalid schedule format. Use 'N hours/days/minutes' (e.g., '1 day').")
    else:
        # Default: create a single video when no flags provided
        orchestrator.create_single_video(topic=args.topic)


if __name__ == "__main__":
    main()
