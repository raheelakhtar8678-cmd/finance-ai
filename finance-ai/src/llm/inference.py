from transformers import AutoModelForCausalLM, AutoTokenizer

class MiniModel:
    """Wrapper so we can swap different models later."""

    def __init__(self, model_name="Qwen/Qwen2.5-0.5B"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)

    def run(self, prompt: str):
        input_ids = self.tokenizer(prompt, return_tensors="pt")
        output = self.model.generate(**input_ids, max_new_tokens=50)
        return self.tokenizer.decode(output[0], skip_special_tokens=True)
