from unittest.mock import MagicMock

import chainlit.server

# Outside the Chainlit runner, chainlit.server.server doesn't exist.
# Stub it so chainlit_app module-level code can be imported in tests.
if not hasattr(chainlit.server, 'server'):
    chainlit.server.server = MagicMock()
