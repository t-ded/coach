import webbrowser

from coach.config.credentials import CredentialsStore

API_KEY_URL = 'https://platform.openai.com/api-keys'


def setup_openai_key() -> None:
    print('\n=== OpenAI Setup ===')
    print('Opening browser to get your API key...')
    print(f'If the browser does not open, visit: {API_KEY_URL}\n')
    webbrowser.open(API_KEY_URL)

    print('Steps:')
    print('1. Sign in to your OpenAI account')
    print('2. Click "Create new secret key"')
    print('3. Copy the key (you will not be able to see it again)\n')

    api_key = _prompt_for_api_key()
    CredentialsStore().store_openai_api_key(api_key)

    print('\n✓ OpenAI API key stored successfully!')
    print('Credentials stored securely in ~/.coach/credentials.json')


def _prompt_for_api_key() -> str:
    while True:
        api_key = input('Paste your OpenAI API key: ').strip()

        if not api_key:
            print('Error: API key cannot be empty.')
            continue

        if not api_key.startswith('sk-'):
            confirmation = input('Warning: Unusual format (does not start with sk-). Continue? (y/n): ').strip().lower()
            if confirmation != 'y':
                continue

        return api_key

    raise ValueError('Unable to collect OpenAI API key')
