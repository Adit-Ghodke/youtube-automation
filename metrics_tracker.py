import json
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class MetricsTracker:
    """Tracks performance and cost metrics for video creation."""

    def __init__(self, metrics_file: str = "metrics.json"):
        self.metrics_file = Path(metrics_file)
        self.load_metrics()

    def load_metrics(self):
        """Loads metrics from the JSON file."""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file) as f:
                    self.data = json.load(f)
            except json.JSONDecodeError:
                logger.warning("Metrics file is corrupted. Starting with a new one.")
                self._initialize_metrics()
        else:
            self._initialize_metrics()

    def _initialize_metrics(self):
        """Initializes a new metrics structure."""
        self.data = {
            "total_videos": 0,
            "successful_uploads": 0,
            "failed_runs": 0,
            "total_api_cost": 0.0,
            "videos": []
        }

    def save_metrics(self):
        """Saves the current metrics to the JSON file."""
        with open(self.metrics_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def record_video(self, video_data: dict):
        """
        Records the outcome of a video creation attempt.
        This is the method that was missing.
        """
        self.data["total_videos"] += 1
        
        if video_data.get("success"):
            self.data["successful_uploads"] += 1
        else:
            self.data["failed_runs"] += 1
        
        cost = video_data.get("api_cost", 0)
        if isinstance(cost, (int, float)):
            self.data["total_api_cost"] += cost
        
        # Add a record for this specific video run
        self.data["videos"].append({
            "timestamp": datetime.now().isoformat(),
            "topic": video_data.get("topic", "N/A"),
            "success": video_data.get("success"),
            "duration_seconds": video_data.get("duration"),
            "video_id": video_data.get("video_id"),
            "cost": cost
        })
        
        self.save_metrics()
        logger.info("Metrics have been updated.")

    def get_summary(self):
        """Returns a summary of all metrics."""
        success_rate = (
            (self.data["successful_uploads"] / self.data["total_videos"]) * 100
            if self.data["total_videos"] > 0 else 0
        )
        summary = {
            "Total Videos Processed": self.data["total_videos"],
            "Successful Uploads": self.data["successful_uploads"],
            "Failed Runs": self.data["failed_runs"],
            "Success Rate": f"{success_rate:.1f}%",
            "Total Estimated Cost": f"${self.data['total_api_cost']:.2f}"
        }
        return summary

