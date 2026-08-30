import asyncio
import sys
import os

# Add backend directory to sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from dotenv import load_dotenv
load_dotenv(os.path.join(backend_path, ".env"))

from groq import AsyncGroq, APIError, AuthenticationError

async def test_groq_key():
    api_key = os.getenv("GROQ_API_KEY", "")
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    
    print(f"Testing Groq API key: {api_key[:12]}... (length: {len(api_key)})")
    print(f"Target model: {model}")
    
    if not api_key:
        print("ERROR: GROQ_API_KEY is empty in .env")
        return

    try:
        client = AsyncGroq(api_key=api_key)
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hello, answer in 5 words."}],
            max_tokens=30
        )
        print("\n--- GROQ API SUCCESS ---")
        print(f"Response: {response.choices[0].message.content}")
        print(f"Prompt Tokens: {response.usage.prompt_tokens}")
        print(f"Completion Tokens: {response.usage.completion_tokens}")
        print(f"Total Tokens: {response.usage.total_tokens}")
    except AuthenticationError as e:
        print(f"\n--- GROQ API AUTHENTICATION ERROR ---")
        print(f"Status Code: {getattr(e, 'status_code', 'N/A')}")
        print(f"Error Message: {str(e)}")
    except APIError as e:
        print(f"\n--- GROQ API ERROR ---")
        print(f"Status Code: {getattr(e, 'status_code', 'N/A')}")
        print(f"Error Message: {str(e)}")
    except Exception as e:
        print(f"\n--- UNEXPECTED ERROR ---")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_groq_key())
