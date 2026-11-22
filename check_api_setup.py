"""Check whether Taleem Dost AI can read the local .env file.
This script never prints your API key."""
from pathlib import Path
import os
from dotenv import load_dotenv

root = Path(__file__).resolve().parent
env_file = root / ".env"
print("Project folder:", root)
print(".env file exists:", env_file.is_file())
if env_file.is_file():
    load_dotenv(dotenv_path=env_file, override=True)
key = os.getenv("OPENAI_API_KEY", "").strip()
print("OPENAI_API_KEY detected:", bool(key))
print("Key has placeholder value:", key.lower() in ("", "your_api_key_here", "your_actual_api_key_here"))
if not env_file.is_file():
    print("Fix: create a file named .env in this folder, beside main.py.")
elif not key:
    print("Fix: open .env and add OPENAI_API_KEY=your_secret_key on one line.")
elif key.lower() in ("your_api_key_here", "your_actual_api_key_here"):
    print("Fix: replace the placeholder with your real secret key.")
else:
    print("The key is being read. This does not test whether the key is valid or has API billing access.")
