from typing import Optional

import chainlit as cl

from coach.domain.session import Message
from coach.domain.session import Session
from coach.persistence.repositories.messages import SupabaseMessageRepository
from coach.persistence.repositories.sessions import SupabaseSessionRepository
from coach.reasoning.summarizer import SessionSummarizer
from coach.web import coaching
from coach.web import session


def _format_date(s: Session) -> str:
    return s.last_message_at.strftime('%b %d, %H:%M')


def _build_session_panel(sessions: list[Session], current_session_id: Optional[str]) -> tuple[str, list[cl.Action]]:
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
    current_session_id: Optional[str] = cl.user_session.get(coaching.SESSION_DB_SESSION_ID)
    text, actions = _build_session_panel(sessions, current_session_id)
    await cl.Message(text, actions=actions).send()


async def handle_cancel_sessions_panel() -> None:
    from coach.web.api_key_flow import ready_actions

    await cl.Message('Chat sessions panel closed.', actions=ready_actions()).send()


def _render_past_messages(messages: list[Message]) -> str:
    lines: list[str] = []
    for msg in messages:
        timestamp = msg.created_at.strftime('%b %d, %H:%M')
        role_label = 'You' if msg.role == 'user' else 'Coach'
        lines.append(f'**{role_label}** ({timestamp}):\n{msg.content}\n')
    return '\n---\n'.join(lines)


def _summary_is_stale(db_session: Session, latest_message_id: Optional[str]) -> bool:
    if db_session.summary is None:
        return True
    if latest_message_id is None:
        return False
    return db_session.summarized_through_message_id != latest_message_id


async def handle_open_session(session_id: str) -> None:
    from coach.web.api_key_flow import ready_actions

    authenticated_client = session.get_authenticated_client()
    user_id = session.get_user_id()

    session_repo = SupabaseSessionRepository(authenticated_client, user_id)
    msg_repo = SupabaseMessageRepository(authenticated_client, user_id)

    db_session = await cl.make_async(session_repo.get)(session_id)
    if db_session is None:
        await cl.Message('Session not found.', actions=ready_actions()).send()
        return

    messages = await cl.make_async(msg_repo.load_for_session)(session_id)

    title = db_session.title or 'Untitled'
    await cl.Message(f'**Resuming session: {title}**').send()

    if messages:
        history_text = _render_past_messages(messages)
        await cl.Message(history_text).send()

    # Generate or use cached summary for coach context
    summary: Optional[str] = None
    if messages:
        latest_id = await cl.make_async(msg_repo.latest_id)(session_id)
        if _summary_is_stale(db_session, latest_id):
            await cl.Message('Generating session summary for the coach...').send()
            provider, api_key = coaching.get_llm_config()
            summarizer = SessionSummarizer(provider=provider, api_key=api_key)
            summary = await cl.make_async(summarizer.generate)(messages)
            if latest_id:
                await cl.make_async(session_repo.update_summary)(session_id, summary, latest_id)
        else:
            summary = db_session.summary

    # Reinitialize coach with session summary
    profile = cl.user_session.get(coaching.SESSION_CURRENT_PROFILE)
    activities = cl.user_session.get(coaching.SESSION_ACTIVITIES)
    display_name = cl.user_session.get(coaching.SESSION_DISPLAY_NAME)
    coaching.init_coach_session(profile, activities, display_name, session_summary=summary)

    cl.user_session.set(coaching.SESSION_DB_SESSION_ID, session_id)
    cl.user_session.set(coaching.SESSION_MESSAGE_COUNT, len(messages))

    await cl.Message('Session restored. You can continue the conversation.', actions=ready_actions()).send()
