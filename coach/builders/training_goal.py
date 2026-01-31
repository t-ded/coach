from coach.builders.utils import compute_distance_duration_pace
from coach.builders.utils import parse_date
from coach.builders.utils import parse_distance_into_meters
from coach.builders.utils import parse_duration
from coach.builders.utils import parse_pace_into_minutes_per_km
from coach.builders.utils import parse_sport_type
from coach.domain.activity import DISTANCE_SPORT_TYPES
from coach.domain.goals import DistanceActivityTrainingGoal
from coach.domain.goals import TrainingGoal


def _strip_bullet_point_line(line: str) -> str:
    return line.lstrip('- ').strip()


def _get_line_title_and_value(line: str) -> tuple[str, str]:
    if not line or ':' not in line:
        return '', ''

    key, value = line.split(':', 1)
    key = key.strip().lower()
    value = value.strip()
    return key, value


def build_training_goal(goal_description: str) -> TrainingGoal:
    """
    Build a TrainingGoal or DistanceActivityTrainingGoal from structured text.

    Expected format:
    - Goal Name
        - Sport: <sport_type>
        - Goal date: <date or N/A>
        - Distance: <distance> (optional, for distance sports)
        - Total duration: <HH:MM:SS> (optional, for distance sports)
        - Pace: <MM:SS/unit> (optional, for distance sports)
        - Notes: <notes> (optional)
    """
    lines = [line.strip() for line in goal_description.strip().split('\n') if line.strip()]

    name = _strip_bullet_point_line(lines[0])

    sport_type = None
    goal_date = 'N/A'
    notes = None
    distance_meters = None
    duration_seconds = None
    pace_str = None

    for line in lines[1:]:
        line = _strip_bullet_point_line(line)
        line_title, line_value = _get_line_title_and_value(line)

        match line_title:
            case 'sport':
                sport_type = parse_sport_type(line_value)
            case 'goal date':
                goal_date = parse_date(line_value)
            case 'notes':
                notes = line_value
            case 'distance':
                distance_meters = parse_distance_into_meters(line_value)
            case 'total duration':
                duration_seconds = parse_duration(line_value)
            case 'pace':
                pace_str = parse_pace_into_minutes_per_km(line_value)

    if not sport_type:
        raise ValueError('Sport type is required')

    if sport_type in DISTANCE_SPORT_TYPES and (distance_meters or duration_seconds or pace_str):
        distance_meters, duration_seconds, pace_str = compute_distance_duration_pace(distance_meters, duration_seconds, pace_str)

        return DistanceActivityTrainingGoal(
            sport_type=sport_type,
            name=name,
            goal_date=goal_date,
            notes=notes,
            goal_distance_meters=distance_meters,
            goal_duration_seconds=duration_seconds,
            goal_pace=pace_str,
        )
    else:
        return TrainingGoal(
            sport_type=sport_type,
            name=name,
            goal_date=goal_date,
            notes=notes,
        )
