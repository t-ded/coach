from coach.reasoning.assistant import build_assistant_prompt


def test_build_assistant_prompt_minimal() -> None:
    result = build_assistant_prompt(system_prompt='You are a coach.')
    assert result == 'System instructions:\nYou are a coach.\nYour answer: <response>'


def test_build_assistant_prompt_all_sections() -> None:
    result = build_assistant_prompt(
        system_prompt='You are a coach.',
        user_system_prompt='Be concise.',
        additional_context='Training data here.',
        chat_history='User: Hello\nAssistant: Hi',
        user_prompt='How am I doing?',
    )
    assert result == (
        'System instructions:\nYou are a coach.\n'
        'User instructions:\nBe concise.\n'
        'Additional context:\nTraining data here.\n'
        'Conversation so far:\nUser: Hello\nAssistant: Hi\n'
        'User question:\nHow am I doing?\n'
        'Your answer: <response>'
    )


def test_build_assistant_prompt_optional_sections_omitted() -> None:
    result = build_assistant_prompt(
        system_prompt='You are a coach.',
        user_system_prompt=None,
        additional_context='Training data here.',
        chat_history=None,
        user_prompt='How am I doing?',
    )
    assert result == ('System instructions:\nYou are a coach.\nAdditional context:\nTraining data here.\nUser question:\nHow am I doing?\nYour answer: <response>')
