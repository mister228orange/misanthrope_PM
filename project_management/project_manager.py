from models import PMContext


context = PMContext()
client = Client(
  host='http://localhost:11434',
  headers={'x-some-header': 'some-value'}
)
deepseek = "deepseek-r1:8b"
response = client.generate(model=deepseek, prompt='')