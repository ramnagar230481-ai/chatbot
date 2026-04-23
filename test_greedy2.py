import asyncio
from model import ChatModel
from config import config

async def test_model():
    model = ChatModel(model_name=config.MODEL_NAME, max_history=config.MAX_HISTORY_LENGTH)
    
    inputs = ["hello", "what can you do?", "what is outlier?"]
    
    for user_input in inputs:
        eos_text = model.tokenizer.eos_token or ""
        new_user_input_ids = model.tokenizer.encode(
            user_input + eos_text,
            return_tensors="pt",
        )
        
        bot_input_ids = new_user_input_ids
        import torch
        attention_mask = torch.ones_like(bot_input_ids)
        with torch.no_grad():
            chat_history_ids = model.model.generate(
                bot_input_ids,
                attention_mask=attention_mask,
                max_new_tokens=80,
                repetition_penalty=1.0,
                do_sample=False,
                no_repeat_ngram_size=3,
                pad_token_id=model.tokenizer.eos_token_id,
                eos_token_id=model.tokenizer.eos_token_id,
            )
        new_tokens = chat_history_ids[:, bot_input_ids.shape[-1] :]
        raw_response = model.tokenizer.decode(new_tokens[0], skip_special_tokens=True).strip()
        print(f"Input: {user_input}")
        print(f"Greedy Output: {raw_response}")

if __name__ == "__main__":
    asyncio.run(test_model())
