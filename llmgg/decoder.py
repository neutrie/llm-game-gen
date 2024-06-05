import json
from enum import Enum
from typing import Any, TypeAlias, cast

from llmgg.game import GameData, Item, Room


class GameDataError(ValueError):
    pass


class GameDataSchema(Enum):
    ROOT = {
        "rooms": list,
    }
    ROOM = {
        "roomStart": bool,
        "roomName": str,
        "roomDescription": str,
        "roomItems": list,
        "roomRequirements": list,
        "roomConnections": dict,
    }
    ITEM = {
        "itemObjective": bool,
        "itemName": str,
        "itemDescription": str,
    }


class GameDataDecoder(json.JSONDecoder):
    JsonValue: TypeAlias = (
        list["JsonValue"] | dict[str, "JsonValue"] | str | bool | int | float | None
    )

    def __init__(self, **kwargs: Any):
        kwargs.setdefault("object_hook", self.game_data_object_hook)
        super().__init__(**kwargs)

        self.item_references: dict[str, Item] = {}
        self.objective_reference: Item | None = None
        self.requirement_requests: dict[str, list[Room]] = {}

        self.room_references: dict[str, Room] = {}
        self.starting_room_reference: Room | None = None
        self.connection_requests: dict[str, list[Room]] = {}

        self.decoders = (
            (GameDataSchema.ROOT, self.decode_root),
            (GameDataSchema.ROOM, self.decode_room),
            (GameDataSchema.ITEM, self.decode_item),
        )

    def game_data_object_hook(self, dct: dict[str, JsonValue]):
        keys_set = set(dct.keys())
        if not keys_set:
            raise GameDataError("Each JSON object must not be empty.")

        expected_fields: set[str] = set()
        for schema, decoder_method in self.decoders:
            schema_keys = schema.value.keys()
            if keys_set.issubset(set(schema_keys)):
                return decoder_method(dct)
            for k in schema_keys:
                expected_fields.add(k)

        unknown_fields = keys_set.difference(expected_fields)
        if unknown_fields:
            raise GameDataError(
                "Unknown field(s) in the JSON object: {}".format(
                    ", ".join(unknown_fields)
                )
            )
        raise GameDataError("JSON object contains field(s) of another object type.")

    def decode_root(self, dct: dict[str, JsonValue]) -> GameData:
        rooms = dct.get("rooms")
        if not rooms or not isinstance(rooms, list):
            raise GameDataError("There must be a non-empty `rooms` array.")
        if not all(isinstance(room, Room) for room in rooms):
            raise GameDataError("Each array element in `rooms` must be a room object.")
        rooms = cast(list[Room], rooms)
        if not self.objective_reference:
            raise GameDataError(
                "There must be at least one item with `itemObjective` field set to "
                "`true`."
            )
        if not self.starting_room_reference:
            raise GameDataError(
                "There must be at least one room with `roomStart` field set to `true`."
            )
        return GameData(
            rooms=rooms,
            objective=self.objective_reference,
            starting_room=self.starting_room_reference,
        )

    def decode_room(self, dct: dict[str, JsonValue]) -> Room:
        room_name = dct.get("roomName")
        if not room_name or not isinstance(room_name, str):
            raise GameDataError("Each room must have a non-empty `roomName` string.")
        room_description = dct.get("roomDescription")
        if not room_description or not isinstance(room_description, str):
            raise GameDataError(
                "Each room must have a non-empty `roomDescription` string."
            )
        room = Room(name=room_name, description=room_description)
        room_start = dct.get("roomStart")
        if room_start is not None and not isinstance(room_start, bool):
            raise GameDataError(
                f"In room `{room_name}`, the field `roomStart` must be a boolean."
            )
        if room_start:
            if self.starting_room_reference:
                raise GameDataError(
                    "There must be only one room with the `roomStart` field set to "
                    "`true`."
                )
            self.starting_room_reference = room
        room_items = dct.get("roomItems")
        if room_items is not None and not isinstance(room_items, list):
            raise GameDataError(
                f"In room `{room_name}`, the field `roomItems` must be an array."
            )
        if room_items:
            for item in room_items:
                if not isinstance(item, Item):
                    raise GameDataError(
                        f"In room `{room_name}`, in the field `roomItems`, each array "
                        "element must be an item object."
                    )
                room.items.append(item)
        room_requirements = dct.get("roomRequirements")
        if room_requirements is not None and not isinstance(room_requirements, list):
            raise GameDataError(
                f"In room `{room_name}`, the field `roomRequirements` must be an array."
            )
        if room_requirements:
            for item_name in room_requirements:
                if not item_name or not isinstance(item_name, str):
                    raise GameDataError(
                        f"In room `{room_name}`, in the field `roomRequirements`, each "
                        "array element must be a non-empty string."
                    )
                existing_item = self.item_references.get(item_name)
                # ignore the requirements located in the room itself
                if existing_item and existing_item not in room.items:
                    room.requirements.append(existing_item)
                else:
                    self.requirement_requests.setdefault(item_name, [])
                    self.requirement_requests[item_name].append(room)
        room_connections = dct.get("roomConnections")
        if room_connections is not None and not isinstance(room_connections, list):
            raise GameDataError(
                f"In room `{room_name}`, the field `roomConnections` must be an array."
            )
        if room_connections:
            for connected_room_name in room_connections:
                if not connected_room_name or not isinstance(connected_room_name, str):
                    raise GameDataError(
                        f"In room `{room_name}`, in the field `roomConnections`, each "
                        "array element must be a non-empty string."
                    )
                existing_room = self.room_references.get(connected_room_name)
                if existing_room:
                    room.connections.append(existing_room)
                elif connected_room_name != room_name:
                    self.connection_requests.setdefault(connected_room_name, [])
                    self.connection_requests[connected_room_name].append(room)
        requested_connection = self.connection_requests.pop(room_name, None)
        if requested_connection:
            for requester in requested_connection:
                requester.connections.append(room)
        self.room_references[room_name] = room
        return room

    def decode_item(self, dct: dict[str, JsonValue]) -> Item:
        item_name = dct.get("itemName")
        if not item_name or not isinstance(item_name, str):
            raise GameDataError("Each item must have a non-empty `itemName` string.")
        item_description = dct.get("itemDescription")
        if not item_description or not isinstance(item_description, str):
            raise GameDataError(
                "Each item must have a non-empty `itemDescription` string."
            )
        item = Item(name=item_name, description=item_description)
        item_objective = dct.get("itemObjective")
        if item_objective is not None and not isinstance(item_objective, bool):
            raise GameDataError(
                f"In item `{item_name}`, the field `itemObjective` must be a boolean."
            )
        if item_objective:
            if self.objective_reference:
                raise GameDataError(
                    "There must be only one item with the `itemObjective` field set to "
                    "`true`."
                )
            self.objective_reference = item
        requested_requirement = self.requirement_requests.pop(item_name, None)
        if requested_requirement:
            for requester in requested_requirement:
                requester.requirements.append(item)
        self.item_references[item_name] = item
        return item
