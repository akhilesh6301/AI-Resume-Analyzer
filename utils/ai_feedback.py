import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai.errors import ServerError, ClientError

# Load .env file from the project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Get API Key
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

# Initialize Gemini Client
client = genai.Client(api_key=api_key)


def analyze_resume(resume_text, job_description):
    prompt = f"""
You are an expert ATS Resume Analyzer.

Analyze the following resume against the given job description.

Resume:
{resume_text}

Job Description:
{job_description}

Return your response in exactly this format:

ATS Score:
<number only>

Strengths:
- Point 1
- Point 2
- Point 3

Missing Skills:
- Skill 1
- Skill 2
- Skill 3

Suggestions:
- Suggestion 1
- Suggestion 2
- Suggestion 3

Final Recommendation:
One short paragraph.
"""

    max_retries = 5

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=prompt
            )

            return response.text

        except ServerError as e:
            print("=" * 60)
            print(f"Server busy (Attempt {attempt + 1}/{max_retries})")
            print(e)
            print("=" * 60)

            if attempt < max_retries - 1:
                print("Retrying in 10 seconds...\n")
                time.sleep(10)

        except ClientError as e:
            print("=" * 60)
            print("Client Error")
            print(e)
            print("=" * 60)
            break

        except Exception as e:
            print("=" * 60)
            print("Unexpected Error")
            print(type(e))
            print(e)
            print("=" * 60)
            break

    # Fallback response
    return """
ATS Score:
N/A

Strengths:
- Resume uploaded successfully.

Missing Skills:
- AI analysis unavailable.

Suggestions:
- Gemini API is temporarily unavailable.
- Please try again after a few minutes.
- Your ATS score could not be generated at this time.

Final Recommendation:
The resume was uploaded successfully, but the AI service is currently unavailable due to high server demand. Please try again later.
"""