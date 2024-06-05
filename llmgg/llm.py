from typing import cast

import ollama


def generate_response(
    model: str,
    system_prompt: str,
    chat_history: list[tuple[str, str]],
    user_prompt: str,
    options: ollama.Options = ollama.Options(temperature=0.69),
) -> str:
    messages: list[ollama.Message] = []
    messages.append(ollama.Message(role="system", content=system_prompt))
    for prompt, response in chat_history:
        messages.append(ollama.Message(role="user", content=prompt))
        messages.append(ollama.Message(role="assistant", content=response))
    messages.append(ollama.Message(role="user", content=user_prompt))
    chat_response = cast(
        ollama.ChatResponse,
        ollama.chat(
            model=model,
            messages=messages,
            stream=False,
            format="",
            options=options,
            keep_alive=0,
        ),
    )
    return chat_response["message"]["content"]
