import json

from network import protocol

# Every protocol Command/Response is a plain class whose __init__ params
# match its attribute names 1:1, so `cls(**obj.__dict__)` reconstructs any
# of them - no per-class (de)serialization code needed.
_REGISTRY = {name: cls for name, cls in vars(protocol).items() if isinstance(cls, type)}


def serialize(obj):
    data = dict(obj.__dict__)
    # GameStateUpdated.state is a real GameState (Board/Piece/Motion objects
    # underneath) - not JSON-serializable as-is, so flatten it if it knows how.
    state = data.get("state")
    if state is not None and hasattr(state, "to_dict"):
        data["state"] = state.to_dict()
    return json.dumps({"type": type(obj).__name__, "data": data})


def deserialize(text):
    payload = json.loads(text)
    cls = _REGISTRY[payload["type"]]
    return cls(**payload["data"])
