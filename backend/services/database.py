# SecureIT360 - Database Connection File
# This file connects the backend to your Supabase database.
# Every other file will import this to talk to the database.

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load the secret keys from the .env file
load_dotenv()

# Get the Supabase URL and keys from .env
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Create two connections:
# 1. Regular connection - for normal user actions
# 2. Service connection - for admin actions like creating tenants
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)