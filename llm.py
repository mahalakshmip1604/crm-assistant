import os
import time
from dotenv import load_dotenv
from openai import OpenAI, APIConnectionError, APIStatusError, RateLimitError, APITimeoutError

load_dotenv()

BASE_URL = os.getenv("LLM_BASE_URL")
API_KEY = os.getenv("LLM_API_KEY")
MODEL = os.getenv("LLM_MODEL")

# Fail early with a clear message if .env is missing or incomplete
missing = [name for name, val in
           [("LLM_BASE_URL", BASE_URL), ("LLM_API_KEY", API_KEY), ("LLM_MODEL", MODEL)]
           if not val]
if missing:
    raise SystemExit(f"Missing in .env: {', '.join(missing)}. "
                     "Check the file is named exactly .env and sits in the project root.")

client = OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=90, max_retries=0)


def ask(messages, json_mode=False, retries=3):
    """Send chat messages to the LLM and return the reply text."""
    kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}

    for attempt in range(1, retries + 1):
        try:
            r = client.chat.completions.create(
                model=MODEL, messages=messages, temperature=0, **kwargs
            )
            return r.choices[0].message.content

        except RateLimitError:
            # Free tier limit (HTTP 429): wait and try again
            wait = 5 * attempt
            print(f"Rate limit hit, retrying in {wait}s (attempt {attempt}/{retries})...")
            time.sleep(wait)

        except APIStatusError as e:
            if e.status_code == 401 or e.status_code == 403:
                raise SystemExit("Authentication failed: check LLM_API_KEY in .env.")
            if e.status_code == 404:
                raise SystemExit(f"Model not found: '{MODEL}'. Check LLM_MODEL in .env.")
            raise SystemExit(f"API error {e.status_code}: {e.message}")

        except APIConnectionError as e:
            print(f"Base URL used: {BASE_URL!r}")
            raise SystemExit(f"Cannot reach the API. Cause: {e.__cause__!r}")
        
        except APITimeoutError:
            raise SystemExit("Request timed out after 30s. The network or the model is too slow.")

    raise SystemExit("Still rate limited after retries. Wait a minute and try again.")


if __name__ == "__main__":
    print(f"Using model: {MODEL}")
    print(ask([{"role": "user", "content": "Say hello in one sentence."}]))