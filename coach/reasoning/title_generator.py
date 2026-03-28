_MAX_TITLE_LENGTH = 50


def generate_title(first_message: str) -> str:
    text = first_message.strip()
    if not text:
        return 'New chat'
    text = text.replace('\n', ' ')
    if len(text) <= _MAX_TITLE_LENGTH:
        return text
    truncated = text[:_MAX_TITLE_LENGTH]
    last_space = truncated.rfind(' ')
    if last_space > 0:
        truncated = truncated[:last_space]
    return truncated + '...'
