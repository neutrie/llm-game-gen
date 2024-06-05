import importlib.resources
import json
from pathlib import Path

from llmgg.decoder import GameDataDecoder
from llmgg.game import GameData

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
