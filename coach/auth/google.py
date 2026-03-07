import webbrowser

from coach.config.credentials import CredentialsStore

API_KEY_URL = 'https://aistudio.google.com/apikey'


def setup_google_ai_key() -> None:
    print('\n=== Google AI Studio Setup ===')
    print('Opening browser to get your free API key...')
    print(f'If the browser does not open, visit: {API_KEY_URL}\n')
    webbrowser.open(API_KEY_URL)

    print('Steps:')
    print('1. Sign in with your Google account')
    print('2. Click "Create API key"')
    print('3. Copy the key\n')

    api_key = _prompt_for_api_key()
    CredentialsStore().store_google_api_key(api_key)

    print('\n✓ Google AI API key stored successfully!')
    print('Credentials stored securely in ~/.coach/credentials.json')


def _prompt_for_api_key() -> str:
    while True:
        api_key = input('Paste your Google AI API key: ').strip()

        if not api_key:
            print('Error: API key cannot be empty.')
            continue

        if not api_key.startswith('AIza'):
            confirmation = input('Warning: Unusual format (does not start with AIza). Continue? (y/n): ').strip().lower()
            if confirmation != 'y':
                continue

        return api_key

    raise ValueError('Unable to collect Google AI API key')
