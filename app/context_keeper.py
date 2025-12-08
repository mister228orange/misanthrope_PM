from datetime import date, datetime
from typing import Optional, List, Tuple
from pathlib import Path
import pandas as pd

from misanthrope_pm.core.models import ClosedTask
from misanthrope_pm.data.loader import load_closed_tasks, load_git_logs
from misanthrope_pm.data.validator import validate_data


class PMContext:
    """Main context manager for project data"""

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        # Load and validate data
        print("Loading project data...")
        self.closed_tasks = load_closed_tasks(self.data_dir / "closed_tasks")
        self.git_logs = load_git_logs(self.data_dir / "git.logs")

        # Validate data quality
        validation_result = validate_data(self.closed_tasks, self.git_logs)
        if not validation_result.is_valid:
            print(f"Warning: Data validation issues: {validation_result.issues}")

        # Preprocess data
        self._preprocess_data()

        print(f"Loaded {len(self.closed_tasks)} tasks and {len(self.git_logs)} commits")

    def _preprocess_data(self):
        """Preprocess loaded data for analysis"""
        if not self.git_logs.empty:
            # Remove initial commit if it's empty/initial
            if len(self.git_logs) > 1:
                first_commit = self.git_logs.iloc[0]
                if any(keyword in first_commit.get("title", "").lower()
                       for keyword in ["initial", "init", "first"]):
                    self.git_logs = self.git_logs.iloc[1:]

            # Calculate daily stats
            self.daily_stats = self._calculate_daily_stats()
        else:
            self.daily_stats = pd.DataFrame()

    def _calculate_daily_stats(self) -> pd.DataFrame:
        """Calculate daily productivity statistics"""
        daily = (
            self.git_logs
            .groupby("day")
            .agg(
                commits=("title", "count"),
                insertions=("insertions", "sum"),
                deletions=("deletions", "sum")
            )
            .reset_index()
        )
        daily["net_changes"] = daily["insertions"] - daily["deletions"]
        daily["avg_commit_size"] = (daily["insertions"] + daily["deletions"]) / daily["commits"]
        return daily

    def get_tasks(
            self,
            from_date: Optional[date] = None,
            to_date: Optional[date] = None,
            category: Optional[str] = None
    ) -> List[ClosedTask]:
        """Get tasks filtered by date range and category"""
        filtered = []

        for task in self.closed_tasks:
            # Date filter
            if from_date and task.finished_at and task.finished_at.date() < from_date:
                continue
            if to_date and task.finished_at and task.finished_at.date() > to_date:
                continue

            # Category filter
            if category and task.category.value != category:
                continue

            filtered.append(task)

        return filtered

    def get_logs(
            self,
            from_date: Optional[date] = None,
            to_date: Optional[date] = None
    ) -> pd.DataFrame:
        """Get git logs filtered by date range"""
        if self.git_logs.empty:
            return pd.DataFrame()

        mask = pd.Series(True, index=self.git_logs.index)

        if from_date:
            mask = mask & (self.git_logs["day"] >= from_date)
        if to_date:
            mask = mask & (self.git_logs["day"] <= to_date)

        return self.git_logs[mask].copy()

    def get_daily_stats(self) -> pd.DataFrame:
        """Get daily productivity statistics"""
        return self.daily_stats.copy()

    def get_summary(self) -> dict:
        """Get project summary"""
        return {
            "total_tasks": len(self.closed_tasks),
            "total_commits": len(self.git_logs),
            "date_range": {
                "first_task": min((t.finished_at for t in self.closed_tasks if t.finished_at), default=None),
                "last_task": max((t.finished_at for t in self.closed_tasks if t.finished_at), default=None),
                "first_commit": self.git_logs["day"].min() if not self.git_logs.empty else None,
                "last_commit": self.git_logs["day"].max() if not self.git_logs.empty else None,
            },
            "categories": {
                cat.name: len([t for t in self.closed_tasks if t.category == cat])
                for cat in Category
            }
        }