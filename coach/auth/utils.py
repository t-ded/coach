def no_credentials_found_message(source: str) -> str:
    if source.lower() not in {'strava', 'google', 'openai'}:
        raise ValueError(f'Unsupported data source: {source}')
    return f'No {source.capitalize()} credentials found.' + '\n' + f'Run "coach auth setup" or "coach auth {source.lower()}" to setup authentication for {source.capitalize()}'
