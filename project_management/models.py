from enum import Enum
from typing import Any, Optional
from dataclasses import dataclass
from pathlib import Path

from utils import load_git_logs


class Category(Enum):
    I = 'I'
    F = 'F'
    B = 'B'

class SkillLevel(Enum):
    junior = 'junior'
    middle = 'middle'
    senior = 'senior'
    architecture = 'architecture'   

    
    
@dataclass
class ClosedTask:
    text: str
    category: Category
    estimated_time: Optional[int]
    min_skill_level: Optional[SkillLevel]


def load_closed_tasks() -> list[ClosedTask]:
    folder_path = Path('./closed_tasks') 
    tasks = []
    for file_path in folder_path.iterdir():
        # Check if the item is actually a file
        if file_path.is_file():
            with open(file_path, 'r') as f:
                tasks += [
                    ClosedTask(text=line[:-3], 
                            category=Category(line[-2]), 
                            estimated_time=None, 
                            min_skill_level=None)
                    for line in f.readlines()
                    ]

    return tasks

class Commit:
    def __init__(self, text: str):
        self.text = text


class PMContext:

    def __init__(self) -> None:
        self.closed_tasks = load_closed_tasks()
        print(self.closed_tasks)
        self.git_logs = load_git_logs()[:-1]  #init commit broke stats
        print(self.git_logs)
        self.daily = (
            self.git_logs
                .groupby("day")
                .agg(
                    insertions=("insertions", "sum"),
                    deletions=("deletions", "sum"),
                    commits=("title", "count")
                )
                .reset_index()
        )

        print("\nDaily summary:\n", self.daily)
        print(f"avg insertions per day: {self.daily.insertions.mean()}")
        print(f"avg deletions per day: {self.daily.deletions.mean()}")


