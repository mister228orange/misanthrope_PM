from ollama import Client


class QualityRater:
    def __init__(self, model_name="gemma3:4b"):
        self.base_prompt = 'You are Rater of quality reverse git  analysts. Your main task - \
              give right rate of predicted tasks of solved by commits and real life state\
                  \nOutput is just one float number from 0 to 1: where 0 absolutly bullshit from reverse analyst and 1 is full matching'\
                  'No additional information, just one number.'


        self.llm_client = Client(
            host='http://localhost:11434',
            headers={'x-some-header': 'some-value'}
        )
        self.model_name = model_name

    def _parse_response(self, response) -> float:
        try:
            if self.model_name.startswith("deepseek"):
                _, thinking, answer = response.response.split("think>")
                print(f"deepthink: {thinking}\nanswer: {answer}")
                return float(answer)
            if self.model_name.startswith("gemma"):
                return float(response.response)
        except Exception as e:
            return -1.1



    def rate(self, llm_predict, original) -> float:
        prompt_tail = f'predicted tasks {llm_predict}\noriginal tasks:{original}'
        response = self.llm_client.generate(
            model=self.model_name, 
            prompt=self.base_prompt+prompt_tail
        )
        print(response, response.response)
        return self._parse_response(response)
    
    def stable_rate(self, llm_predict, original, attempts=10) -> float:
        rates = [self.rate(llm_predict, original) for i in range(attempts)]
        print(rates)
        rates = [r for r in rates if r>=0]
        return sum(rates)/len(rates)



tasks1 = ['create jinja2 template for .env for new clients I',
'update docker compose on staging to unclude new containers redis celery etc I',
'create script to generate client.env file I',
'fix workers CRUDs B']

tasks2 = ['create workflow to auto clients app generating I',
'update docker compose on staging to unclude new containers redis celery etc I',
'create script to generate client.env file I',
'fix workers get and read functions B']

qa = QualityRater("deepseek-r1:8b")
print(f' Tasks match for {int(qa.stable_rate(tasks1, tasks2) * 100)} %')