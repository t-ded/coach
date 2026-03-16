from enum import StrEnum


class ProfileParts(StrEnum):
    CHAT_PREFERENCES = 'chat preferences'
    TRAINING_PREFERENCES = 'training preferences'
    PERSONAL_INFORMATION = 'personal information'
    CONSTRAINTS = 'constraints'
    GOALS = 'goals'


SECTION_INTROS: dict[str, str] = {
    ProfileParts.CHAT_PREFERENCES: (
        '--- Chat Preferences ---\n'
        'How would you like to be coached? Describe your preferences for response style, tone, length, and language.'
    ),
    ProfileParts.TRAINING_PREFERENCES: (
        '--- Training Preferences ---\n'
        'How do you like to train? Describe workout types you enjoy or dislike, how you structure your sessions, recovery habits, etc.'
    ),
    ProfileParts.PERSONAL_INFORMATION: (
        '--- Personal Background ---\n'
        'Tell me about yourself — your fitness history and sports background, current activity level, occupation, and any relevant health context.'
    ),
    ProfileParts.CONSTRAINTS: (
        '--- Constraints ---\n'
        'What are your training constraints? Think about available days per week, time-of-day preferences, scheduling limits, and any injuries or physical restrictions.'
    ),
    ProfileParts.GOALS: (
        '--- Goals ---\n'
        'What are your training goals? For each goal, describe the target (time, distance, weight, etc.), sport, timeline, and how important it is to you. Also any additional related notes.'
    ),
}

_CHAT_PREFERENCES_PROMPT = """
You are collecting a user's chat preferences for an AI coaching assistant.

The user has already provided their initial answer. If you need to clarify or want more detail, ask clear follow up questions with direct answers. Aim to understand:
- Response length and detail level (concise vs. thorough)
- Tone (motivational, analytical, direct, casual, etc.)
- Language or communication style

When you have enough information, respond with exactly: DONE
"""

_TRAINING_PREFERENCES_PROMPT = """
You are collecting a user's training preferences for an AI coaching assistant.

The user has already provided their initial answer. If you need to clarify or want more detail, ask clear follow up questions with direct answers. Aim to understand:
- Preferred workout types and structures
- Training approaches they enjoy or actively dislike
- Recovery habits and preferences

When you have enough information, respond with exactly: DONE
"""

_PERSONAL_INFORMATION_PROMPT = """
You are collecting personal background from a user for an AI coaching assistant.

The user has already provided their initial answer. If you need to clarify or want more detail, ask clear follow up questions with direct answers. Aim to understand:
- Age and general fitness history
- Current activity level and sports background
- Occupation or lifestyle factors that affect training (energy, available time)
- Any relevant health or injury history

Only ask what is relevant to coaching. When you have enough information, respond with exactly: DONE
"""

_CONSTRAINTS_PROMPT = """
You are collecting a user's training constraints for an AI coaching assistant.

The user has already provided their initial answer. If you need to clarify or want more detail, ask clear follow up questions with direct answers. Aim to understand:
- Maximum training days per week
- Time-of-day preferences
- Scheduling limitations
- Any injuries or physical restrictions to respect

When you have enough information, respond with exactly: DONE
"""

_GOALS_PROMPT = """
You are collecting a user's training goals for an AI coaching assistant.

The user has already provided their initial answer. If you need to clarify or want more detail, ask clear follow up questions with direct answers. For each goal, aim to confirm:
- Specific performance target (time, distance, weight, etc.)
- Sport type
- Goal date or whether it is open-ended
- Priority level
- Any notes on how they want to approach or prepare for it

When you have confirmed all goals, respond with exactly: DONE
"""

CONVERSATION_PROMPTS: dict[str, str] = {
    ProfileParts.CHAT_PREFERENCES: _CHAT_PREFERENCES_PROMPT.strip(),
    ProfileParts.TRAINING_PREFERENCES: _TRAINING_PREFERENCES_PROMPT.strip(),
    ProfileParts.PERSONAL_INFORMATION: _PERSONAL_INFORMATION_PROMPT.strip(),
    ProfileParts.CONSTRAINTS: _CONSTRAINTS_PROMPT.strip(),
    ProfileParts.GOALS: _GOALS_PROMPT.strip(),
}
