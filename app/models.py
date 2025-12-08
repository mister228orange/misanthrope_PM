from enum import Enum
from typing import Any, Optional
from dataclasses import dataclass



class Category(Enum):
    I = 'I'
    F = 'F'
    B = 'B'

class SkillLevel(Enum):
    junior = 'junior'
    middle = 'middle'
    senior = 'senior'
    architect = 'architect'

    
    
@dataclass
class ClosedTask:
    text: str
    category: Category
    estimated_time: Optional[int]
    min_skill_level: Optional[SkillLevel]
    planned_at: Optional[int]
    started_at: Optional[int]
    finished_at: Optional[int]


class Commit:
    def __init__(self, text: str):
        self.text = text



