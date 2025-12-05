from asyncio import Task
from typing import Any
from models import ClosedTask
from ollama import Client
import pandas as pd

class GitReverseAnalyst:
    def __init__(self, tasks):

        self.etalon_tasks = tasks
        self.setup_prompt = f"base on this tasks to find optimal abstract level of setted tasks, and separate close to original. {self.etalon_tasks}"
        self.base_prompt = 'You are a project manager assistant.\
              Analyze the following git logs and extract discrete tasks that were completed.\
                  \nOutput in a structured format: { tasks:[task description, category (B/F/I)], unfinished_moves[*where in free format describe for your future analyze context of previous state*].\
                  \nLogs:\n{logs}'
        
        self.client = Client(
            host='http://localhost:11434',
            headers={'x-some-header': 'some-value'}
            )
        deepseek = "deepseek-r1:8b"    

    def analyze_git_logs(self, logs: pd.DataFrame) -> list[ClosedTask]:
        g = logs.groupby(pd.Grouper(key='Date', freq='week'))
        chunks = [group for name, group in g]
        tasks_doiting = []
        for chunk in chunks:
            response = analyze_chunk(chunk, [])
            tasks, unfinished_moves = parse_response(response)
    

    def analyze_chunk(self, chunk: pd.DataFrame, unfinished_moves: list[str]) -> [Any Any Any]:


        prompt_tail = f"Previous context{unfinished_moves}"
        full_prompt = f"{self.setup_prompt}\n{self.base_prompt}\n{prompt_tail} {chunk.to_json()}"
        yield self.client.generate(model="deepseek-r1:8b", prompt = full_prompt)