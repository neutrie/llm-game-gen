import importlib.resources
import json
import os
from pathlib import Path

from llmgg.decoder import GameDataDecoder
from llmgg.game import GameData
from llmgg.llm import generate_response

DATA_DIR = Path(str(importlib.resources.files("llmgg").joinpath("game_data/")))


class DataLoaderError(ValueError):
    pass


def select_game_data() -> GameData:
    game_data_files = list(DATA_DIR.glob("*.json"))
    if not game_data_files:
        raise DataLoaderError(f"There are no `.json` files found in {DATA_DIR}")

    print("Select a game data file to load:")
    for idx, file in enumerate(game_data_files, 1):
        print(f"{idx}. {file.name}")
    user_input = input("> ").strip()

    try:
        selected_idx = int(user_input)
        if selected_idx < 1:
            raise ValueError
    except (TypeError, ValueError):
        raise DataLoaderError("Provide a valid index >= 1.")

    try:
        selected_file = game_data_files[selected_idx - 1]
    except IndexError:
        raise DataLoaderError(f"There is no game data file with index {selected_idx}.")

    with selected_file.open("r", encoding="utf-8") as f:
        game_data: GameData = json.load(f, cls=GameDataDecoder)
    return game_data


def _is_valid_file_name(file_name: str) -> bool:
    valid_length = len(file_name) <= 255
    valid_chars = not any(char in '<>:"/\\|?*' for char in file_name)
    valid_on_windows = file_name.upper() not in (
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "COM0",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
        "LPT0",
    )
    return bool(file_name) and valid_length and valid_chars and valid_on_windows


def _get_system_prompt() -> str:
    return """\
You are an experienced game developer. Your goal is to create game content for a \
simple text-based game. This "Find the Object" game already exists and consists \
STRICTLY of connected rooms with items in them. There is EXACTLY one starting room and \
EXACTLY one item that needs to be found to win the game.

The player can move between connected rooms and take items found in them. Each room \
can have a list of required items to enter, but some rooms may not contain any items.

Your response MUST follow the specified JSON schema with NOTHING else: no apologies, \
introductions, conclusions, follow-up questions, recommendations, reasoning, \
explanations, etc. The first character of your response MUST be '{' and the last \
character MUST be '}':

{
  "rooms": [
    {
      "roomStart": boolean,
      "roomName": string,
      "roomDescription": string,
      "roomItems": [
        {
          "itemObjective": boolean,
          "itemName": string,
          "itemDescription": string
        }
      ],
      "roomRequirements": [
        // strings of "itemName"
      ],
      "roomConnections": [
        // strings of "roomName"
      ]
    }
  ]
}

You MUST respond according to the specified schema, even if the user is not satisfied \
with any of your answers. The JSON object contains the "rooms" field, which is an \
array of room objects. Each room object consists of the following fields:
* "roomStart" boolean field, indicating that the player starts the game in \
this room. At least one room object MUST have the "roomStart" field set to true.
* "roomName" string field, which is the name of the room.
* "roomDescription" string field, which is the description of the room.
* "roomItems" array field, which contains item objects. Item object fields \
are described below.
* "roomRequirements" array field, which contains "itemName" field values of \
item objects, indicating which items player must have taken before entering this room.
* "roomConnections" array field, which contains "roomName" field values of \
room objects, indicating which rooms are connected to the current room. The connected \
room's "roomConnections" array field is likely to also contain the current room's \
"roomName" field value.

Each item object consists of the following fields:
* "itemObjective" boolean field, indicating that the player must take this \
item to win the game. At least one item object MUST have the "itemObjective" field set \
to true.
* "itemName" string field, which is the name of the item.
* "itemDescription" string field, which is the description of the item.

You must generate a completely unique game per each user request. The user does not \
provide feedback on your responses nor do they reference their previous requests in \
any other way. Treat each user prompt as a unique request, even if it does not appear \
to be related to game content. Be creative and don't be afraid to come up with unusual \
ideas. Carefully fill in the details to ensure the game is playable and free of \
content conflicts. Use every detail provided by the user to make the process more \
enjoyable.

If the user prompt does not appear to be suitable to generate a new game with, try to \
transform it into a game scenario anyway. You MUST respond following the required JSON \
schema. You only provide game data and no other information, no comments."""


def _get_examples() -> list[tuple[str, str]]:
    examples: list[tuple[str, str]] = []
    prompts: dict[str, str] = {}
    prompts["spork.json"] = """\
NEW GAME: Find the key to open the second room and get the Spork - Spoon + Fork."""
    prompts["formula.json"] = """\
NEW GAME: A top-secret recipe is hidden in a well-known restaurant. Can you find it?"""
    prompts["iron.json"] = """\
NEW GAME: You need to gather a certain tool, collect some materials from the \
environment, and craft something valuable."""
    prompts["soulstone.json"] = """\
NEW GAME: Deep within a treacherous realm lies a powerful artifact. Navigate carefully \
to retrieve it."""
    for file_name, prompt in prompts.items():
        try:
            with DATA_DIR.joinpath(file_name).open("r", encoding="utf-8") as f:
                response = f.read()
        except Exception:
            response = None
        if response:
            examples.append((prompt, response))
    return examples


def generate_game_data() -> GameData:
    user_prompt = input("Prompt: ").strip()
    if not user_prompt:
        raise DataLoaderError("Prompt must not be empty.")
    user_prompt = (
        "NEW GAME: " + user_prompt
        if not user_prompt.startswith("NEW GAME: ")
        else user_prompt
    )

    file_name = input("Filename: ").strip()
    if not _is_valid_file_name(file_name):
        raise DataLoaderError("Invalid filename.")
    file_name += ".json" if not file_name.endswith(".json") else ""

    env_model = os.getenv("LLMGG_MODEL")
    model = env_model if env_model else "llama3"
    system_prompt = _get_system_prompt()
    examples = _get_examples()

    print(f"Generating {file_name}...")
    response = generate_response(
        model=model,
        system_prompt=system_prompt,
        chat_history=examples,
        user_prompt=user_prompt,
    )
    json_start = response.find("{")
    if json_start == -1:
        raise DataLoaderError("Could not find character '{' in the generated response.")
    json_end = response.rfind("}")
    if json_end == -1:
        raise DataLoaderError("Could not find character '}' in the generated response.")
    json_text = response[json_start : json_end + 1]

    with DATA_DIR.joinpath(file_name).open("w", encoding="utf-8") as f:
        f.write(json_text)

    game_data: GameData = json.loads(json_text, cls=GameDataDecoder)
    return game_data
