from typing import Optional

import chainlit as cl

from coach.domain.session import Message
from coach.domain.session import Session
from coach.persistence.repositories.messages import SupabaseMessageRepository
from coach.persistence.repositories.sessions import SupabaseSessionRepository
from coach.reasoning.summarizer import SessionSummarizer
from coach.reasoning.title_generator import generate_title
from coach.web import coaching
from coach.web import session

SESSION_DB_SESSION_ID = 'db_session_id'
SESSION_MESSAGE_COUNT = 'message_count'
SESSION_PENDING_RENAME = 'pending_rename_session_id'
SESSION_PENDING_PROMOTE = 'pending_promote_session_id'


async def save_message_pair(user_content: str, assistant_content: str) -> None:
    db_session_id: Optional[str] = cl.user_session.get(SESSION_DB_SESSION_ID)
    if not db_session_id:
        return

    authenticated_client = session.get_authenticated_client()
    user_id = session.get_user_id()
    msg_repo = SupabaseMessageRepository(authenticated_client)
    session_repo = SupabaseSessionRepository(authenticated_client, user_id)

    await cl.make_async(msg_repo.save)(db_session_id, 'user', user_content)
    await cl.make_async(msg_repo.save)(db_session_id, 'assistant', assistant_content)
    await cl.make_async(session_repo.update_last_message_at)(db_session_id)

    count: int = cl.user_session.get(SESSION_MESSAGE_COUNT, default=0)
    if count == 0:
        title = generate_title(user_content)
        await cl.make_async(session_repo.update_title)(db_session_id, title)
    cl.user_session.set(SESSION_MESSAGE_COUNT, count + 1)


def _format_date(s: Session) -> str:
    return s.last_message_at.strftime('%b %d, %H:%M')


def _short_title(s: Session) -> str:
    title = s.title or 'Untitled'
    return title[:30] + '...' if len(title) > 30 else title


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
                lines.append(f'- {_short_title(s)} — {_format_date(s)}')
            lines.append('')

        if unnamed:
            lines.append('**Recent**')
            for s in unnamed:
                lines.append(f'- {_short_title(s)} — {_format_date(s)}')

    actions: list[cl.Action] = []

    for s in named + unnamed:
        label = _short_title(s)
        if s.id != current_session_id:
            actions.append(cl.Action(name='open_session', payload={'session_id': s.id}, label=f'Open: {label}'))
        if s.session_type == 'named':
            actions.append(cl.Action(name='rename_session', payload={'session_id': s.id}, label=f'Rename: {label}'))
        if s.session_type == 'unnamed':
            actions.append(cl.Action(name='promote_session', payload={'session_id': s.id, 'title': s.title or ''}, label=f'Save as thread: {label}'))
        actions.append(cl.Action(name='delete_session', payload={'session_id': s.id}, label=f'Delete: {label}'))

    actions.append(cl.Action(name='cancel_sessions_panel', payload={}, label='Cancel'))

    return '\n'.join(lines), actions


async def handle_sessions_panel() -> None:
    authenticated_client = session.get_authenticated_client()
    user_id = session.get_user_id()
    session_repo = SupabaseSessionRepository(authenticated_client, user_id)
    sessions = await cl.make_async(session_repo.list_for_user)()
    current_session_id: Optional[str] = cl.user_session.get(SESSION_DB_SESSION_ID)
    text, actions = _build_session_panel(sessions, current_session_id)
    await cl.Message(text, actions=actions).send()


async def handle_cancel_sessions_panel() -> None:
    from coach.web.api_key_flow import ready_actions

    await cl.Message('Chat sessions panel closed.', actions=ready_actions()).send()


async def handle_delete_session(session_id: str) -> None:
    authenticated_client = session.get_authenticated_client()
    user_id = session.get_user_id()
    session_repo = SupabaseSessionRepository(authenticated_client, user_id)
    await cl.make_async(session_repo.delete)(session_id)

    current_session_id: Optional[str] = cl.user_session.get(SESSION_DB_SESSION_ID)
    if session_id == current_session_id:
        new_session = await cl.make_async(session_repo.create)()
        cl.user_session.set(SESSION_DB_SESSION_ID, new_session.id)
        cl.user_session.set(SESSION_MESSAGE_COUNT, 0)

    await cl.Message('Session deleted.').send()
    await handle_sessions_panel()


async def handle_rename_session(session_id: str) -> None:
    cl.user_session.set(SESSION_PENDING_RENAME, session_id)
    await cl.Message('Type the new title for this session:').send()


async def handle_rename_input(user_input: str) -> bool:
    pending_id: Optional[str] = cl.user_session.get(SESSION_PENDING_RENAME)
    if not pending_id:
        return False

    cl.user_session.set(SESSION_PENDING_RENAME, None)
    authenticated_client = session.get_authenticated_client()
    user_id = session.get_user_id()
    session_repo = SupabaseSessionRepository(authenticated_client, user_id)
    new_title = user_input.strip()
    if new_title:
        await cl.make_async(session_repo.update_title)(pending_id, new_title)
        await cl.Message(f'Session renamed to "{new_title}".').send()
    else:
        await cl.Message('Rename cancelled (empty title).').send()
    await handle_sessions_panel()
    return True


async def handle_promote_session(session_id: str, default_title: str) -> None:
    cl.user_session.set(SESSION_PENDING_PROMOTE, session_id)
    prompt = 'Enter a title for this thread'
    if default_title:
        prompt += f' (or send "{default_title}" to keep the current title)'
    await cl.Message(f'{prompt}:').send()


async def handle_promote_input(user_input: str) -> bool:
    session_id: Optional[str] = cl.user_session.get(SESSION_PENDING_PROMOTE)
    if not session_id:
        return False

    cl.user_session.set(SESSION_PENDING_PROMOTE, None)
    title = user_input.strip()

    authenticated_client = session.get_authenticated_client()
    user_id = session.get_user_id()
    session_repo = SupabaseSessionRepository(authenticated_client, user_id)

    if title:
        await cl.make_async(session_repo.promote)(session_id, title)
        await cl.Message(f'Saved as thread: "{title}".').send()
    else:
        await cl.make_async(session_repo.promote)(session_id)
        await cl.Message('Saved as thread.').send()

    await handle_sessions_panel()
    return True


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
    msg_repo = SupabaseMessageRepository(authenticated_client)

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

    coaching.reinit_coach_from_session(session_summary=summary)

    cl.user_session.set(SESSION_DB_SESSION_ID, session_id)
    cl.user_session.set(SESSION_MESSAGE_COUNT, len(messages))

    await cl.Message('Session restored. You can continue the conversation.', actions=ready_actions()).send()
