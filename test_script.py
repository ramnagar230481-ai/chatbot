import asyncio
from model import ChatModel
from config import config

async def test_model():
    print("Loading model...")
    model = ChatModel(model_name=config.MODEL_NAME, max_history=config.MAX_HISTORY_LENGTH)
    print("Model loaded. Testing generation...")
    
    response = model.generate_response("Hello!")
    print(f"Response 1: {response}")
    
    response = model.generate_response("How are you?")
    print(f"Response 2: {response}")

if __name__ == "__main__":
    asyncio.run(test_model())
