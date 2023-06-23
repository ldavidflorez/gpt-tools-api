import openai

import os

openai.api_key = os.environ["OPENAI_API_KEY"]


def get_response(prompt: str):
    # generate the response
    response = openai.Completion.create(
        engine=os.environ["ENGINE"],
        prompt=prompt,
        temperature=float(os.environ["TEMPERATURE"]),
        max_tokens=int(os.environ["MAX_TOKENS"]),
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=["12."]
    )

    return response
