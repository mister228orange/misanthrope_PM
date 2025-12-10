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

def to_int(num):
    try:
        return int(num)
    except Exception as e:
        return None
    
@dataclass
class ClosedTask:
    text: str
    category: Category
    estimated_time: Optional[int]
    min_skill_level: Optional[SkillLevel]
    planned_at: Optional[int]
    started_at: Optional[int]
    finished_at: Optional[int]
    lines_added: Optional[int]
    lines_removed: Optional[int]
    

    def __init__(self, text: str, category: str, **data: dict):
        self.text = text
        self.category = Category(category)
        data.pop("text")
        data.pop("category")
        
        
        for key, value in data.items():
            # Handle specific fields
            if key == "estimated_time":
                self.estimated_time = to_int(value) if value is not None else None
            elif key == "min_skill_level":
                if isinstance(value, SkillLevel):
                    self.min_skill_level = value
                elif value is not None:
                    self.min_skill_level = SkillLevel(value)
            elif key == "planned_at":
                self.planned_at = to_int(value) if value is not None else None
            elif key == "started_at":
                self.started_at = to_int(value) if value is not None else None
            elif key == "finished_at":
                self.finished_at = to_int(value) if value is not None else None
            elif key == "lines_added":
                self.lines_added = to_int(value) if value is not None else None
            elif key == "lines_removed":
                self.lines_removed = to_int(value) if value is not None else None
            
        # (text=line[:-3],
        #     category=Category(line.strip()[-1]),
        #     estimated_time=None,
        #     min_skill_level=None,
        #     planned_at=None,
        #     started_at=None,
        #     finished_at=int(datetime(datetime.now().year, datetime.strptime(file_path.stem.split('_')[0], '%B').month, 30, 21, 20, 0).timestamp())
        #     )

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



