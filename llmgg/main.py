import sys
from json import JSONDecodeError

from llmgg.decoder import GameDataError
from llmgg.game import Player
from llmgg.loader import select_game_data


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def main() -> int:
    try:
        game_data = select_game_data()
    except JSONDecodeError as e:
        eprint(f"ERROR: Unable to parse JSON: {e}")
        return 1
    except GameDataError as e:
        eprint(f"ERROR: Incorrect game data: {e}")
        return 2
    except Exception as e:
        eprint(f"ERROR: Failed to load game data: {e}")
        return 3
    player = Player(
        starting_room=game_data.starting_room,
        objective=game_data.objective,
    )

    INFO = f"""
--------------------
Available commands:
`rooms`
    Check the connections of the current room.
`items`
    Check the items of the current room.
`inventory`
    Check the inventory.
`go 'idx'`
    Go to the room with index 'idx' in the connections of the current room.
`take 'idx'`
    Take the item with index 'idx' from the current room.
`help`, `?`
    Show this message.
`quit`, `exit`
    Exit the game.

Objective: {game_data.objective}
Starting room: {game_data.starting_room}
--------------------
"""
    print(INFO)
    should_exit = False
    while not should_exit:
        print()
        command = [s.strip().casefold() for s in input("> ").split(sep=" ") if s]
        match command:
            case ["rooms"]:
                print(player.check_rooms())
            case ["items"]:
                print(player.check_items())
            case ["inventory"]:
                print(player.check_inventory())
            case ["go", *idx]:
                try:
                    idx = int(idx.pop(0))
                    if idx < 1:
                        raise ValueError
                except (IndexError, TypeError, ValueError):
                    print("Provide a valid index >= 1.")
                    continue
                print(player.go(idx))
            case ["take", *idx]:
                try:
                    idx = int(idx.pop(0))
                    if idx < 1:
                        raise ValueError
                except (IndexError, TypeError, ValueError):
                    print("Provide a valid index >= 1.")
                    continue
                result, found_objective = player.take_item(idx)
                print(result)
                should_exit = True if found_objective else False
            case ["help"] | ["?"]:
                print(INFO)
            case ["quit"] | ["exit"]:
                print("Thanks for playing!")
                should_exit = True
            case _:
                print("Command is not recognized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
