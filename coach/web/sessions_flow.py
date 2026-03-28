from typing import Optional

import chainlit as cl

from coach.domain.session import Session
from coach.persistence.repositories.sessions import SupabaseSessionRepository
from coach.web import coaching
from coach.web import session


def _format_date(s: Session) -> str:
    return s.last_message_at.strftime('%b %d, %H:%M')


def _build_session_panel(sessions: list[Session]) -> tuple[str, list[cl.Action]]:
    named = [s for s in sessions if s.session_type == 'named']
    unnamed = [s for s in sessions if s.session_type == 'unnamed']

    lines: list[str] = ['**Chat Sessions**\n']

    if not named and not unnamed:
        lines.append('No previous sessions yet.')
    else:
        if named:
            lines.append('**Threads**')
            for s in named:
                title = s.title or 'Untitled'
                lines.append(f'- {title} — {_format_date(s)}')
            lines.append('')

        if unnamed:
            lines.append('**Recent**')
            for s in unnamed:
                title = s.title or 'Untitled'
                lines.append(f'- {title} — {_format_date(s)}')

    actions: list[cl.Action] = []

    current_session_id: Optional[str] = cl.user_session.get(coaching.SESSION_DB_SESSION_ID)
    for s in named + unnamed:
        if s.id == current_session_id:
            continue
        label = s.title or 'Untitled'
        actions.append(cl.Action(name='open_session', payload={'session_id': s.id}, label=f'Open: {label}'))

    actions.append(cl.Action(name='cancel_sessions_panel', payload={}, label='Cancel'))

    return '\n'.join(lines), actions


async def handle_sessions_panel() -> None:
    authenticated_client = session.get_authenticated_client()
    user_id = session.get_user_id()
    session_repo = SupabaseSessionRepository(authenticated_client, user_id)
    sessions = await cl.make_async(session_repo.list_for_user)()
    text, actions = _build_session_panel(sessions)
    await cl.Message(text, actions=actions).send()


async def handle_cancel_sessions_panel() -> None:
    from coach.web.api_key_flow import ready_actions

    await cl.Message('Chat sessions panel closed.', actions=ready_actions()).send()
