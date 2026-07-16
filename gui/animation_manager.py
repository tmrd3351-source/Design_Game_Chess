from model.piece import REST_SHORT, REST_LONG
from gui.image import load_animation_config, load_animation_frames

# model.Piece.state (engine-owned: idle/moving/jumping) -> the animation
# clip that state *drives*. Only used the moment the model state (or the
# piece's rest_type) changes; after that the clip's own config.json
# (next_state_when_finished) takes over for non-looping clips.
DRIVEN_CLIP_BY_MODEL_STATE = {
    "moving": "move",
    "jumping": "jump",
    "idle": "idle",
}

# model.Piece.get_rest_type() -> the rest clip it drives while the piece
# sits idle on cooldown. REST_NONE has no entry here, so an idle piece with
# no active cooldown falls back to DRIVEN_CLIP_BY_MODEL_STATE's "idle".
REST_CLIP_BY_REST_TYPE = {
    REST_LONG: "long_rest",
    REST_SHORT: "short_rest",
}


class AnimationManager:
    """Per-piece animation playback, driven by model.Piece.get_state() and
    model.Piece.get_rest_type() - read-only, so this class can never gate
    real move legality, only display it."""

    def __init__(self):
        self._cache = {}  # (code, state) -> (config, frames)
        self._tracked = {}  # piece.id -> {clip, start_time, last_model_state, last_rest_type}

    def _clip_data(self, code, clip):
        key = (code, clip)
        if key not in self._cache:
            self._cache[key] = (
                load_animation_config(code, clip),
                load_animation_frames(code, clip),
            )
        return self._cache[key]

    def _driven_clip(self, model_state, rest_type):
        if model_state == "idle" and rest_type in REST_CLIP_BY_REST_TYPE:
            return REST_CLIP_BY_REST_TYPE[rest_type]
        return DRIVEN_CLIP_BY_MODEL_STATE[model_state]

    def get_frame(self, piece, code, now):
        entry = self._tracked.get(piece.id)
        model_state = piece.get_state()
        rest_type = piece.get_rest_type()
        driven_clip = self._driven_clip(model_state, rest_type)

        if entry is None:
            entry = {
                "clip": driven_clip,
                "start_time": now,
                "last_model_state": model_state,
                "last_rest_type": rest_type,
            }
            self._tracked[piece.id] = entry
        elif model_state != entry["last_model_state"] or rest_type != entry["last_rest_type"]:
            entry["clip"] = driven_clip
            entry["start_time"] = now
            entry["last_model_state"] = model_state
            entry["last_rest_type"] = rest_type
        else:
            config, frames = self._clip_data(code, entry["clip"])
            if not config["graphics"]["is_loop"]:
                elapsed = now - entry["start_time"]
                frame_index = int(elapsed * config["graphics"]["frames_per_sec"])
                if frame_index >= len(frames):
                    entry["clip"] = config["physics"]["next_state_when_finished"]
                    entry["start_time"] = now

        config, frames = self._clip_data(code, entry["clip"])
        elapsed = now - entry["start_time"]
        frame_index = int(elapsed * config["graphics"]["frames_per_sec"])
        if config["graphics"]["is_loop"]:
            frame_index %= len(frames)
        else:
            frame_index = min(frame_index, len(frames) - 1)

        return frames[frame_index]
