from __future__ import annotations

import re
from typing import Optional

from coach.domain.activity import Activity
from coach.domain.activity import Split
from coach.domain.activity import SportType
from coach.domain.activity_intensity import ActivityIntensityProfile
from coach.domain.activity_intensity import PaceZone
from coach.domain.activity_intensity import ZoneDistribution
from coach.domain.personal_bests import RunningPersonalBestsSummary

_10K_TO_5K_RATIO = 0.93


def _pace_str_to_speed_ms(pace_str: str) -> Optional[float]:
    match = re.match(r'(\d+):(\d+)/km', pace_str)
    if not match:
        return None
    seconds_per_km = int(match.group(1)) * 60 + int(match.group(2))
    if seconds_per_km <= 0:
        return None
    return 1000.0 / seconds_per_km


def _resolve_speeds(pb_summary: RunningPersonalBestsSummary) -> Optional[tuple[float, float]]:
    v5k = _pace_str_to_speed_ms(pb_summary.PB_5K.pace_str) if pb_summary.PB_5K else None
    v10k = _pace_str_to_speed_ms(pb_summary.PB_10K.pace_str) if pb_summary.PB_10K else None

    if v5k is None and v10k is None:
        return None
    if v5k is None:
        v5k = v10k / _10K_TO_5K_RATIO  # type: ignore[operator]
    if v10k is None:
        v10k = v5k * _10K_TO_5K_RATIO
    if v10k >= v5k:
        v10k = v5k * _10K_TO_5K_RATIO

    return v5k, v10k


def _assign_zone(speed_ms: float, v5k: float, v10k: float) -> PaceZone:
    if speed_ms >= v5k:
        return PaceZone.Z5_VO2MAX
    if speed_ms >= v10k * 0.92:
        return PaceZone.Z4_THRESHOLD
    if speed_ms >= v5k * 0.80:
        return PaceZone.Z3_TEMPO
    if speed_ms >= v5k * 0.75:
        return PaceZone.Z2_EASY
    return PaceZone.Z1_RECOVERY


def _build_zone_distribution(splits: list[Split], v5k: float, v10k: float) -> list[ZoneDistribution]:
    accum: dict[PaceZone, tuple[float, int]] = {}

    for split in splits:
        if split.average_speed_ms <= 0:
            continue
        zone = _assign_zone(split.average_speed_ms, v5k, v10k)
        prev_dist, prev_time = accum.get(zone, (0.0, 0))
        accum[zone] = (prev_dist + split.distance_meters, prev_time + split.moving_time_seconds)

    return [ZoneDistribution(zone=zone, distance_meters=dist, time_seconds=time) for zone, (dist, time) in sorted(accum.items(), key=lambda kv: kv[0].value)]


def _detect_split(splits: list[Split]) -> Optional[bool]:
    if len(splits) < 2:
        return None

    mid = len(splits) // 2
    first_half = splits[:mid]
    second_half = splits[mid:]

    first_total_dist = sum(s.distance_meters for s in first_half)
    second_total_dist = sum(s.distance_meters for s in second_half)
    if first_total_dist <= 0 or second_total_dist <= 0:
        return None

    first_speed = sum(s.average_speed_ms * s.distance_meters for s in first_half) / first_total_dist
    second_speed = sum(s.average_speed_ms * s.distance_meters for s in second_half) / second_total_dist

    diff_ratio = (second_speed - first_speed) / first_speed
    if abs(diff_ratio) < 0.02:
        return None
    return diff_ratio > 0


def _compute_hr_drift(splits: list[Split]) -> Optional[float]:
    splits_with_hr = [s for s in splits if s.average_heartrate is not None]
    if len(splits_with_hr) < len(splits) * 0.5 or len(splits_with_hr) < 2:
        return None

    mid = len(splits_with_hr) // 2
    first_hr = sum(s.average_heartrate for s in splits_with_hr[:mid]) / mid  # type: ignore[misc]
    second_hr = sum(s.average_heartrate for s in splits_with_hr[mid:]) / len(splits_with_hr[mid:])  # type: ignore[misc]

    return second_hr / first_hr


def _build_flags(
    zone_distribution: list[ZoneDistribution],
    primary_zone: PaceZone,
    total_distance: float,
    is_negative_split: Optional[bool],
    hr_drift: Optional[float],
) -> list[str]:
    flags: list[str] = []

    primary_dist = next((z.distance_meters for z in zone_distribution if z.zone == primary_zone), 0.0)
    pct = int(round(100 * primary_dist / total_distance)) if total_distance > 0 else 0
    zone_label = primary_zone.value.split('/')[1].lower()
    flags.append(f'{primary_zone.value} {zone_label} run ({pct}%)')

    if is_negative_split is True:
        flags.append('negative split — strong finish')
    elif is_negative_split is False:
        flags.append('positive split — faded in second half')

    if hr_drift is not None and hr_drift > 1.05:
        drift_pct = int(round((hr_drift - 1) * 100))
        flags.append(f'HR climbed {drift_pct}% across the run')

    return flags


def build_activity_intensity_profile(
    activity: Activity,
    pb_summary: RunningPersonalBestsSummary,
) -> Optional[ActivityIntensityProfile]:
    if activity.sport_type != SportType.RUN:
        return None
    if not activity.splits:
        return None

    speeds = _resolve_speeds(pb_summary)
    if speeds is None:
        return None

    v5k, v10k = speeds
    zone_distribution = _build_zone_distribution(activity.splits, v5k, v10k)
    if not zone_distribution:
        return None

    primary_zone = max(zone_distribution, key=lambda z: z.time_seconds).zone
    total_distance = sum(z.distance_meters for z in zone_distribution)
    is_negative_split = _detect_split(activity.splits)
    hr_drift = _compute_hr_drift(activity.splits)
    flags = _build_flags(zone_distribution, primary_zone, total_distance, is_negative_split, hr_drift)

    return ActivityIntensityProfile(
        activity_id=activity.id,
        zone_distribution=zone_distribution,
        primary_zone=primary_zone,
        is_negative_split=is_negative_split,
        hr_drift=hr_drift,
        flags=flags,
    )
