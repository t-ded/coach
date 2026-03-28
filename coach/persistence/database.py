import os
from typing import Optional

from supabase import Client
from supabase import create_client

# These are the public project credentials — the anon key is safe to commit
# (Supabase anon keys are public by design; access is controlled by RLS).
# Override with env vars when running your own Supabase project.
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://bcrpnxyjktmqktflgzix.supabase.co')
SUPABASE_ANON_KEY = os.environ.get(
    'SUPABASE_ANON_KEY',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJjcnBueHlqa3RtcWt0Zmxneml4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMyMTQ3NDEsImV4cCI6MjA4ODc5MDc0MX0.G6lQrfd_U1DvA_MzcbN6Py_PhjFC0xEWqqrq7xUne7A',
)

_anon_client: Optional[Client] = None
_secret_client: Optional[Client] = None


def create_anon_client() -> Client:
    global _anon_client
    if _anon_client is None:
        _anon_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    return _anon_client


def create_secret_client() -> Client:
    global _secret_client
    if _secret_client is None:
        _secret_client = create_client(SUPABASE_URL, os.environ['SUPABASE_SECRET_KEY'])
    return _secret_client
