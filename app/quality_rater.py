from ollama import Client


class QualityRater:
    def __init__(self):
        self.base_prompt = 'You are Rater of quality reverse git  analysts. Your main task - \
              give right rate of predicted tasks of solved by commits and real life state\
                  \nOutput is just one float number from 0 to 1: where 0 absolutly bullshit from reverse analyst and 1 is full matching'


        self.llm_client = Client(
            host='http://localhost:11434',
            headers={'x-some-header': 'some-value'}
        )
        self.model_name = "gemma3:4b"

    def rate(self, llm_predict, original) -> float:
        prompt_tail = f'predicted tasks {llm_predict}\noriginal tasks:{original}'
        res = self.llm_client.generate(model=self.model_name, prompt=self.base_prompt+prompt_tail)
        print(res)
        return 0



tasks1 = ['create jinja2 template for .env for new clients I',
'update docker compose on staging to unclude new containers redis celery etc I',
'create script to generate client.env file I',
'fix workers CRUDs B']
tasks2 = ['create workflow to auto clients app generating I',
'update docker compose on staging I',
'fix workers get and read functions B']

qa = QualityRater()
qa.rate(tasks1, tasks2)