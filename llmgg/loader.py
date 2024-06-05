import importlib.resources
import json
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


def generate_game_data() -> GameData:
    user_prompt = input("Prompt: ").strip()
    if not user_prompt:
        raise DataLoaderError("Prompt must not be empty.")

    file_name = input("Filename: ").strip()
    if not _is_valid_file_name(file_name):
        raise DataLoaderError("Invalid filename.")
    file_name += ".json" if not file_name.endswith(".json") else ""

    print(f"Generating {file_name}...")
    response = generate_response()
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
