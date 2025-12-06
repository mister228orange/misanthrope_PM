from ollama import Client
from models import PMContext


context = PMContext()
llm_client = Client(
  host='http://localhost:11434',
  headers={'x-some-header': 'some-value'}
)
deepseek = "gemma3:4b"
response = llm_client.generate(model=deepseek, prompt='')