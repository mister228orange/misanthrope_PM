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
    

    def __str__(self):
        base =  f'{self.text} {self.category}'
        if self.estimated_time:
            base += f'\nEstimated time: {self.estimated_time} h'
        if self.min_skill_level:
            base += f'\nSkill need to: {self.min_skill_level}'
        return base


class Commit:
    def __init__(self, text: str):
        self.text = text



