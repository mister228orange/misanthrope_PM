from datetime import date, datetime
from typing import Optional, List, Tuple
from pathlib import Path
import pandas as pd # type: ignore

from models import Category, ClosedTask
from utils import load_closed_tasks, load_git_logs



class PMContext:
    """Main context manager for project data"""

    def __init__(self, data_dir: str = "../data", project_title="nodis_project"):
        self.data_dir = Path(data_dir) / project_title
        print(self.data_dir)
        self.data_dir.mkdir(exist_ok=True)

        # Load and validate data
        print("Loading project data...")
        self.closed_tasks = load_closed_tasks(self.data_dir / "closed_tasks")
        self.git_logs = load_git_logs(str(self.data_dir / "git.logs"))

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
            from_date: Optional[datetime] = None,
            to_date: Optional[datetime] = None,
            category: Optional[str] = None
    ) -> List[ClosedTask]:
        """Get tasks filtered by date range and category"""
        filtered = []
        if from_date:
            from_timestamp = from_date.timestamp()
        if to_date:
            to_timestamp = to_date.timestamp()

        for task in self.closed_tasks:
            # Date filter
            if from_date and task.finished_at and task.finished_at > from_timestamp:
                continue
            if to_date and task.finished_at and task.finished_at < to_timestamp:
                continue

            # Category filter
            if category and task.category.value != category:
                continue

            filtered.append(task)

        return filtered

    def get_logs(
            self,
            from_date: Optional[datetime] = None,
            to_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Get git logs filtered by date range"""
        if self.git_logs.empty:
            return pd.DataFrame()

        mask = pd.Series(True, index=self.git_logs.index)

        if from_date:
            mask = mask & (self.git_logs["day"] >= from_date)
        if to_date:
            mask = mask & (self.git_logs["day"] <= to_date)

        return self.git_logs[mask].copy() # type: ignore

    def get_daily_stats(self) -> pd.DataFrame:
        """Get daily productivity statistics"""
        return self.daily_stats.copy()

    def get_summary(self) -> dict:
        """Get project summary"""
        return {
            "total_tasks": len(self.closed_tasks),
            "total_commits": len(self.git_logs),
            "date_range": {
                "first_task": datetime.fromtimestamp(min((t.finished_at for t in self.closed_tasks if t.finished_at), default=None)), #type: ignore
                "last_task": datetime.fromtimestamp(max((t.finished_at for t in self.closed_tasks if t.finished_at), default=None)), #type: ignore
                "first_commit": self.git_logs.index.min() if not self.git_logs.empty else None,
                "last_commit": self.git_logs.index.max() if not self.git_logs.empty else None,
            },
            "categories": {
                cat.name: len([t for t in self.closed_tasks if t.category == cat])
                for cat in Category
            }
        }


context = PMContext()
print(context.closed_tasks)
print(context.git_logs)
print(context.get_summary())
