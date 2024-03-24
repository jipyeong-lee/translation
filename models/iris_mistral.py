from transformers import AutoModelForCausalLM, AutoTokenizer, StoppingCriteria, StoppingCriteriaList
import torch
from utils.simple_bleu import simple_score
import torch

# repo = "/work/kollm/LLaMA-Factory/outputs/mistralai-Mistral-7B-Instruct-v0.2-trans-346k-sft-lora-lr1e-5-e1-b4/checkpoint-15000"
# model = AutoModelForCausalLM.from_pretrained(repo, torch_dtype=torch.bfloat16, device_map='auto')
# tokenizer = AutoTokenizer.from_pretrained(repo)
model = None
tokenizer = None

class StoppingCriteriaSub(StoppingCriteria):
    def __init__(self, stops=[], encounters=1):
        super().__init__()
        self.stops = [stop for stop in stops]

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor):
        for stop in self.stops:
            if torch.all((stop == input_ids[0][-len(stop):])).item():
                return True

        return False


stop_words_ids = torch.tensor(
    [[829, 45107, 29958], [1533, 45107, 29958], [829, 45107, 29958], [21106, 45107, 29958]]).to("cuda")
stopping_criteria = StoppingCriteriaList([StoppingCriteriaSub(stops=stop_words_ids)])

def load_model(path):
    global model, tokenizer
    print('load_model', path)
    model = AutoModelForCausalLM.from_pretrained(path, torch_dtype=torch.bfloat16, device_map='auto')
    tokenizer = AutoTokenizer.from_pretrained(path)


def generate(prompt):
    gened = model.generate(
        **tokenizer(
            prompt,
            return_tensors='pt',
            return_token_type_ids=False
        ).to("cuda"),
        max_new_tokens=2048,
        temperature=0.9,
        num_beams=5,
        stopping_criteria=stopping_criteria
    )
    result = tokenizer.decode(gened[0][1:]).replace(prompt + " ", "").replace("</끝>", "")
    result = result.replace('</s>', '')
    result = result.replace('### 한국어: ', '')
    result = result.replace('### 영어: ', '')
    return result


def translate_ko2en(text):
    prompt = f"[INST] 다음 문장을 영어로 번역하세요.{text} [/INST]"
    return generate(prompt)


def translate_en2ko(text):
    prompt = f"[INST] 다음 문장을 한글로 번역하세요.{text} [/INST]"
    return generate(prompt)


def main():
    while True:
        text = input('>')
        en_text = translate_ko2en(text)
        ko_text = translate_en2ko(en_text)
        print('en_text', en_text)
        print('ko_text', ko_text)
        print('score', simple_score(text, ko_text))
    """ 
    >>? 3천만 개가 넘는 파일과 250억 개의 토큰이 있습니다. Phi1.5의 데이터 세트 구성에 접근하지만 오픈 소스 모델인 Mixtral 8x7B를 사용하고 Apache2.0 라이선스에 따라 라이선스가 부여됩니다. 
en_text We have 30 million files and 2.5 billion tokens. We approach Phi1.5's dataset composition, but we use the open-source model, Mixtral 8x7B, and we are licensed according to the Apache2.0 license.
ko_text 3,000만 개의 파일과 250억 개의 토큰이 있습니다. Phi1.5의 데이터 집합에 접근하지만 오픈 소스 모델인 Mixtral 8x7B를 사용하고 Apache2.0 라이선스에 따라 라이선스를 받았습니다.
score 0.6154733407407874
    """

if __name__ == "__main__":
    main()
