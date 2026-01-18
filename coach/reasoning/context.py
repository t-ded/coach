from datetime import UTC
from datetime import datetime

from coach.domain.models import ActivityVolume
from coach.domain.models import SportType
from coach.domain.models import TrainingState
from coach.utils import days_ago


def _summarize_sport_volume(*, sport: SportType, volume: ActivityVolume) -> str:
    summary = f'- {sport.value}: '
    summary += f'{volume.num_activities} activities, '
    summary += f'{volume.duration_seconds // 60} minutes'
    summary += f', {int(volume.distance_meters)} meters' if volume.distance_meters is not None else ''
    return summary


def render_training_state_for_reasoning(training_state: TrainingState) -> str:
    lines: list[str] = []

    lines.append(f'Training window: {training_state.window_start} to {training_state.window_end}')

    current_date = datetime.now(tz=UTC)
    lines.append(f'Snapshot generated at: {training_state.generated_at} ({days_ago(training_state.generated_at)} days ago)')
    lines.append(f'Current date: {current_date}')

    lines.append('Volume by sport:')
    for sport, volume in training_state.volume_by_sport.items():
        lines.append(_summarize_sport_volume(sport=sport, volume=volume))

    if training_state.last_activity_date:
        lines.append(f'Last activity date: {training_state.last_activity_date} ({days_ago(training_state.last_activity_date)} days ago)')

    return '\n'.join(lines)
