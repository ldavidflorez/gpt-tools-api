import openai_async
import json

import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ["OPENAI_API_KEY"]
model = os.environ["ENGINE"]
temperature = float(os.environ["TEMPERATURE"])
max_tokens = int(os.environ["MAX_TOKENS"])


async def get_response(prompt: str):
    # generate the response
    response = await openai_async.complete(
        api_key,
        timeout=10,
        payload={
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
    )

    return json.loads(response.text)
