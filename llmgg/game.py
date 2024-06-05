from dataclasses import dataclass, field


@dataclass
class Item:
    name: str
    description: str

    def __str__(self):
        return f"{self.name} - {self.description}."


@dataclass
class Room:
    name: str
    description: str
    items: list[Item] = field(default_factory=list)
    requirements: list[Item] = field(default_factory=list)
    connections: list["Room"] = field(default_factory=list)

    def __str__(self):
        return f"{self.name} - {self.description}."


@dataclass
class GameData:
    rooms: list[Room]
    objective: Item
    starting_room: Room


class Player:
    def __init__(self, starting_room: Room, objective: Item):
        self.current_room = starting_room
        self.objective = objective
        self.inventory: list[Item] = []

    def check_rooms(self) -> str:
        connected_rooms: list[str] = [
            f"{idx}. {room.name}"
            for idx, room in enumerate(self.current_room.connections, 1)
        ]
        return (
            "\n".join(connected_rooms)
            if connected_rooms
            else "There are no connected rooms. You are stuck."
        )

    def check_items(self) -> str:
        room_items: list[str] = [
            f"{idx}. {item}" for idx, item in enumerate(self.current_room.items, 1)
        ]
        return (
            "\n".join(room_items)
            if room_items
            else f"There are no items in `{self.current_room.name}`."
        )

    def check_inventory(self) -> str:
        inventory_items: list[str] = [f"* {item}" for item in self.inventory]
        return (
            "\n".join(inventory_items)
            if inventory_items
            else "There are no items in the inventory."
        )

    def go(self, idx: int) -> str:
        try:
            next_room = self.current_room.connections[idx - 1]
        except IndexError:
            return f"There is no connection with index {idx}."
        can_go = True
        item_names: list[str] = []
        for item in next_room.requirements:
            item_names.append(f"`{item.name}`")
            can_go = True if can_go and item in self.inventory else False
        if can_go:
            self.current_room = next_room
            return f"You went to: {self.current_room}"
        return "You can't go to `{}`, you need: {}.".format(
            next_room.name, ", ".join(item_names)
        )

    def take_item(self, idx: int) -> tuple[str, bool]:
        try:
            item = self.current_room.items.pop(idx - 1)
        except IndexError:
            return f"There is no item with index {idx}.", False
        if item == self.objective:
            return f"You found `{self.objective.name}`!", True
        self.inventory.append(item)
        return f"You took `{item.name}`.", False
