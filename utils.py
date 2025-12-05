import pandas as pd

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
        df = df.set_index("date")
        return df
