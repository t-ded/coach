from coach.domain.models import CoachResponse


def test_coach_response_headers() -> None:
    assert CoachResponse.headers() == ['Summary', 'Observations', 'Recommendations', 'Confidence Notes']


def test_coach_response_field_info() -> None:
    assert CoachResponse.field_info() == {
        'summary': {},
        "observations": {'bullets': True},
        "recommendations": {'bullets': True},
        "confidence_notes": {'optional': True},
    }
