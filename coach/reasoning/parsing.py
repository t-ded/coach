import re
from dataclasses import fields

from coach.domain.models import CoachResponse


class CoachResponseParseError(Exception):
    pass


def _split_sections(text: str, headers: list[str]) -> dict[str, str]:
    header_pattern = '|'.join(map(re.escape, headers))

    pattern = re.compile(
        rf"(?P<header>{header_pattern})\s*:?\s*"        # header anywhere, optional colon
        rf"(?P<body>.*?)(?=(?:{header_pattern})\s*:?\s*|\Z)",  # until the next header or end
        re.DOTALL,
    )

    result: dict[str, str] = {}

    for match in pattern.finditer(text):
        header = match.group('header')
        body = match.group('body').strip()

        if header not in result:
            result[header] = body

    return result


def _parse_bullets(block: str) -> list[str]:
    items: list[str] = []

    for line in block.splitlines():
        line = line.strip()
        if line.startswith('- '):
            items.append(line[2:].strip())

    return items


def parse_coach_response(text: str) -> CoachResponse:
    headers = CoachResponse.headers()
    sections = _split_sections(text, headers)

    missing = [h for h in headers if h not in sections]
    if missing:
        raise CoachResponseParseError(f'Missing sections: {missing}')

    field_map = dict(zip(headers, fields(CoachResponse), strict=True))
    parsed_data: dict = {}
    for header, value in sections.items():
        field = field_map[header]

        parsed_block: str | list[str] | None = _parse_bullets(value) if field.metadata.get('bullets', False) else value.strip()

        if not parsed_block or parsed_block == 'None':
            if not field.metadata.get('optional', False):
                raise CoachResponseParseError(f'Empty section: {header}')
            parsed_block = None

        parsed_data[field.name] = parsed_block

    return CoachResponse(**parsed_data)
