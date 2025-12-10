from pathlib import Path
from typing import Any, Generator
from models import Category, ClosedTask
from ollama import Client, GenerateResponse
import pandas as pd
import json
from datetime import datetime, date


class GitReverseAnalyst:
    def __init__(self, tasks, project_title,model_name="gemma3:12b", data_dir: str = "../data"):
        self.data_dir = Path(data_dir) / project_title
        self.etalon_tasks = tasks
        self.setup_prompt = f"""
            You are a project manager assistant.

            Your job: analyze git commits and extract discrete development tasks.

            You MUST use the reference tasks below to determine:
            - the correct abstraction level,
            - the correct granularity,
            - the correct categorization.

            REFERENCE_TASKS = {self.etalon_tasks}
            STRICT PROTOCOL (READ CAREFULLY AND FOLLOW EXACTLY):

            You MUST produce a **single JSON object** with the following schema:

            {{
            "tasks": [
                {{
                "text": "string - short but complete task description",
                "category": "B | F | I",
                "purpose": "business | health"
                }}
            ],
            "unfinished_moves": "string"
            }}

            Purpose rules:
            - "business" = creates or changes product functionality (features, user value)
            - "health" = refactoring, infra, cleanup, fixes, migrations, tech-debt

            Category explanation:
            - B = Backend
            - F = Frontend
            - I = Infrastructure

            RULES:
            1. Do NOT add fields.
            2. Do NOT rename fields.
            3. Do NOT output comments or explanations.
            4. Do NOT output chain-of-thought.
            5. Do NOT wrap your JSON in code blocks.
            6. If a field has no value, use an empty string "".
            7. If you cannot follow the schema, output:
            {{"tasks": [], "unfinished_moves": ""}}
            """
        
        self.base_prompt = """
            Now analyze the next commit and extract tasks following the protocol. Title is for hinting, do not rate them.
            And dont blind believe them, main data is git commit message.
            """
        
        self.client: Client = Client(
            host='http://localhost:11434',
            headers={'x-some-header': 'some-value'}
        )
        self.model_name = model_name

    def analyze_git_logs(self, logs: pd.DataFrame):
        logs["text_size"] = logs["text"].str.len()
        print(logs["text_size"])
        commits = logs.to_dict('records')
        commits.reverse()
        print(commits[0]['title'], commits[0].keys())
        
        tasks_doiting: list[ClosedTask] = []
        unfinished_moves = ""
        total_chars = 0
        total__time = 0
        for i in range(2, len(commits)):
            attempts = 3
            while attempts > 0:
                try:
                    print(f'Handle {i} commit {commits[i]['title']} with length {commits[i]['text_size']}')
                    total_chars += commits[i]['text_size']
                    response = self.analyze_commit(commits[i], unfinished_moves)
                    print(f'Receive response {"successfully" if response.done else "error"} for {int(response.total_duration / 10 ** 9)} seconds \n Text: {response.response}')
                    total__time += response.total_duration / 10 ** 9
                    tasks, unfinished_moves = self._parse_response(response, commits[i]['timestamp'])
                    tasks_doiting += tasks
                    break
                except Exception as e:
                    print(e)
                    attempts -= 1
            
            yield tasks, None

        print(f"Git Reverse analyst handle {len(commits)} git commits and reinstate\
               {len(tasks_doiting)} tasks with speed of {total_chars / total__time:.2f} chars per second.")
        self.update_project_data(tasks_doiting)
        self.last_handle_speed = total_chars / total__time
        return tasks_doiting, total_chars / total__time
    
    def update_project_data(self, tasks: list[ClosedTask]) -> None:
        # Todo add db and save tody
        predict_dir = self.data_dir / 'predicted_tasks'
        predict_dir.mkdir(exist_ok=True)
        tasks_df = pd.DataFrame(tasks)
        tasks_df['date'] = pd.to_datetime(tasks_df['finished_at'], unit='s')
        tasks_df['month'] = tasks_df['date'].dt.month #type: ignore
        tasks_df = tasks_df.set_index('date')
        g = tasks_df.groupby(pd.Grouper(key='month'))
        chunks = [(name, group) for name, group in g]
        print(chunks)
        for chunk in chunks:
            filename = date(2000, chunk[0], 1).strftime('%B') + f'_{datetime.now().year%1000}.txt' # type: ignore
            chunk[1].to_csv(predict_dir/filename)



    def analyze_commit(self, commit, unfinished_moves=""):
        prompt = f"""
            PREVIOUS_UNFINISHED_MOVES = "{unfinished_moves}"

            COMMIT:
            <commit_text>
            {commit['text'][:100000]}
            </commit_text>

            COMMIT_TITLE: "{commit['title']}"

            STRINGLY Follow the JSON protocol exactly.
            """
        full_prompt = f"{self.setup_prompt}\n{self.base_prompt}\n {prompt}\n{self.setup_prompt}"
        print(f'full_prompt size {len(full_prompt)}')
        if len(full_prompt) > 90000:
            print("too long")
            return [], unfinished_moves
        return self.client.generate(
            model=self.model_name, 
            prompt = full_prompt,
            options={
                "keep_alive": 0,
                "num_predict": 512,
                "temperature": 0,
                }
            )

    def _parse_response(self, response, closed_at):
        text = response.response
        if text.startswith("```"):
            text = "\n".join(text.split('\n')[1:-1])
        result = json.loads(text)
        print(result)
        tasks = [ClosedTask(task["text"], task["category"], task)
            for task in result['tasks']
            ]
        return tasks, result['unfinished_moves']
 
from context_keeper import context


okt_tasks = context.get_tasks(datetime(2025, 10, 1), datetime(2025, 11, 1))
analyst = GitReverseAnalyst(okt_tasks, 'nodis_project')
git_logs = context.get_logs()
git_logs = git_logs[git_logs['title'] != 'initial commit']
print(git_logs)
task_predicted = []
with open("all_predicted_tasks.txt", 'w') as out:
    for tasks, speed in analyst.analyze_git_logs(git_logs): # type: ignore
        task_predicted += tasks
        out.write('\n'+'\n'.join([str(t) for t in tasks]))
        if speed:
            print(f"speed of work for {analyst.model_name} is {speed} chars per second")
            break


# task_predicted = [ClosedTask(text=line[:-2], category=Category(line[-1]),estimated_time=None, min_skill_level=None, planned_at=None, started_at=None, finished_at=None)for line in open("all_predicted_tasks.txt").readlines()]
# print(task_predicted)
# df = pd.DataFrame(task_predicted)
# print(df)


#TODO add to closed tasks line amounts; rename fro task to action add converting from actions to buisness tasks
