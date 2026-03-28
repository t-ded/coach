from coach.reasoning.title_generator import generate_title


def test_short_message_returned_as_is() -> None:
    assert generate_title('Help with my 5K plan') == 'Help with my 5K plan'


def test_empty_input_returns_default() -> None:
    assert generate_title('') == 'New chat'


def test_whitespace_only_returns_default() -> None:
    assert generate_title('   ') == 'New chat'


def test_long_message_truncated_at_word_boundary() -> None:
    long_msg = 'I want to discuss my upcoming marathon training plan for the spring season next year'
    result = generate_title(long_msg)
    assert len(result) <= 53  # 50 + '...'
    assert result.endswith('...')
    assert not result[:-3].endswith(' ')


def test_exact_boundary_not_truncated() -> None:
    msg = 'a' * 50
    assert generate_title(msg) == msg


def test_one_over_boundary_truncated() -> None:
    msg = 'a' * 51
    result = generate_title(msg)
    assert result.endswith('...')


def test_newlines_replaced_with_spaces() -> None:
    assert generate_title('Line one\nLine two') == 'Line one Line two'


def test_multiline_long_message_truncated() -> None:
    msg = 'Hello can you help me\nwith a very long and detailed marathon training plan for next season'
    result = generate_title(msg)
    assert len(result) <= 53
    assert result.endswith('...')
    assert '\n' not in result
