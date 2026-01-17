from dataclasses import asdict
from typing import Any

from coach.training_state.training_state import TrainingState


def serialize_training_state(state: TrainingState) -> dict[str, Any]:
    return asdict(state)
