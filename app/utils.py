from pathlib import Path

import pandas as pd # type: ignore

from models import ClosedTask, Category
from datetime import datetime

def load_closed_tasks(folder_path: Path) -> list[ClosedTask]:

    tasks = []
    for file_path in folder_path.iterdir():
        # Check if the item is actually a file
        if file_path.is_file():
            with open(file_path, 'r') as f:
                tasks += [
                    ClosedTask(text=line[:-3],
                            category=Category(line.strip()[-1]),
                            estimated_time=None,
                            min_skill_level=None,
                               planned_at=None,
                               started_at=None,
                               finished_at=int(datetime(datetime.now().year, datetime.strptime(file_path.stem.split('_')[0], '%B').month, 30, 21, 20, 0).timestamp())
                            )
                    for line in f.readlines()
                    ]

    return tasks

def load_git_logs(filename="git.logs"):
    with open(filename, 'r') as f:
        commit_texts = f.read().split("\n\ncommit ")
        df = pd.DataFrame([
            {
                "text": c,
                "author": c.split('\n')[1].split()[1],
                "date": " ".join(c.split('\n')[2].split()[1:]),
                "title": c.split('\n')[4],
                "insertions": len([line for line in c.split('\n') if line.startswith("+")]),
                "deletions": len([line for line in c.split('\n') if line.startswith("-")])
            } 
        for c in commit_texts
        ])
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["day"] = df["date"].dt.date
        df["timestamp"] = df["date"].apply(pd.Timestamp) #type: ignore
        df = df.set_index("date")
        return df


# def f():
#     i = 1
#     while 1:
#         yield i
#         i += 3
#         if i > 100:
#             return i ** i

# for k in f():
#     print(k)
# finally:
#     print('huy')
