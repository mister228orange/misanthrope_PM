from typing import Any, Generator
from models import ClosedTask
from ollama import Client, GenerateResponse
import pandas as pd
import json


class GitReverseAnalyst:
    def __init__(self, tasks, model_name="gemma3:12b"):

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
                "text": "string - a short but complete description of the task",
                "category": "B | F | I"
                }}
            ],
            "unfinished_moves": "<summary of unresolved tasks or state>"
            }}

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
        
        self.client = Client(
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
        
        tasks_doiting = []
        unfinished_moves = ""
        for i in range(2, len(commits)):
            attempts = 3
            while attempts > 0:
                try:
                    print(f'Handle {i} commit {commits[i]['title']} with length {commits[i]['text_size']}')
                    response = self.analyze_commit(commits[i], unfinished_moves)
                    print(f'Receive response {"successfully" if response.done else "error"} for {int(response.total_duration / 10 ** 9)} seconds \n Text: {response.response}') 
                    tasks, unfinished_moves = self._parse_response(response, commits[i]['timestamp'])
                    tasks_doiting += tasks
                    break
                except Exception as e:
                    print(e)
                    attempts -= 1
            
            yield tasks 
        return tasks_doiting
    

    def analyze_chunk(self, chunk: pd.DataFrame, unfinished_moves: str) -> Generator[GenerateResponse, Any, None]:
        commits = chunk.to_dict('records')
        logs = [f'<commit_text>{commit['text'][:100000]}</commit_text> title:{commit['title']}\n' for commit in commits if 'initial commit' not in commit['title']]
        prompt_tail = f"Previous context{unfinished_moves}" if unfinished_moves else ""
        full_prompt = f"{self.setup_prompt}\n{self.base_prompt}\n{prompt_tail} {logs}"
        
        return self.client.generate(
            model=self.model_name, 
            prompt = full_prompt,
            options={
                "keep_alive": 0,
                "num_predict": 512,
                "temperature": 0.15,
                }
        )


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
        tasks = [ClosedTask(
            text=task['text'], 
            category=task['category'],
            estimated_time=None, 
            min_skill_level=None,
            planned_at=None,
            started_at=None,
            finished_at=int(closed_at.timestamp())
            ) for task in result['tasks']
            ]
        return tasks, result['unfinished_moves']
 
from context_keeper import context
import datetime

okt_tasks = context.get_tasks(datetime.datetime(2025, 10, 1), datetime.datetime(2025, 11, 1))
analyst = GitReverseAnalyst(okt_tasks)
git_logs = context.get_logs()
git_logs = git_logs[git_logs['title'] != 'initial commit']
print(git_logs)
task_predicted = []
with  open("predicted_tasks.txt", 'w') as out:
    for tasks in analyst.analyze_git_logs(git_logs): # type: ignore
        task_predicted += tasks
        out.write('\n'+'\n'.join([str(t) for t in tasks]))

print(task_predicted)
