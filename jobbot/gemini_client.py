import json
import os
import time
import concurrent.futures
from google import genai
from google.genai import types
from jobbot.models import JobAnalysis


def _make_api_call(client, model_name, prompt, config):
    """Helper function to isolate the API call for the ThreadPoolExecutor."""
    return client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config,
    )


def analyze_job_match(
    resume_text: str, job_description: str, min_score: int, model_name: str
) -> dict:
    """
    Sends the resume and JD to Gemini and returns a parsed JSON dictionary.
    Includes a hard timeout and retry loop to prevent phantom freezes.
    """

    try:
        client = genai.Client()
    except Exception as e:
        print(f"[!] Failed to initialize Gemini Client. Check your API key. Error: {e}")
        return {"score": 0, "improvements": "API Client setup failed."}

    # 1. Read the prompt template from the root folder
    try:
        prompt_path = os.path.join(os.getcwd(), "prompts.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        print("[!] prompts.txt not found. Please create it in the root directory.")
        return {"score": 0, "improvements": "Prompt file missing."}

    # 2. Inject the actual resume and JD into the prompt
    final_prompt = prompt_template.format(
        resume=resume_text, min_score=min_score, job_description=job_description
    )

    # 3. Define the strict API configuration
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=JobAnalysis,
        temperature=0.2,
    )

    # 4. Defense Parameters
    MAX_RETRIES = 3
    TIMEOUT_SECONDS = 45

    # 5. Execute with Timeout and Retry Logic
    for attempt in range(MAX_RETRIES):
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    _make_api_call, client, model_name, final_prompt, config
                )

                # If this takes longer than 45 seconds, it physically kills the wait and throws an error
                response = future.result(timeout=TIMEOUT_SECONDS)

            # Parse and return the JSON dictionary
            result_dict = json.loads(response.text)
            return result_dict

        except concurrent.futures.TimeoutError:
            print(
                f"    -> [!] Gemini API timed out on attempt {attempt + 1}/{MAX_RETRIES}."
            )
        except json.JSONDecodeError:
            # This should be exceptionally rare now that you are using response_schema
            print(
                f"    -> [!] Gemini returned invalid JSON on attempt {attempt + 1}/{MAX_RETRIES}."
            )
        except Exception as e:
            print(
                f"    -> [!] Gemini API error on attempt {attempt + 1}/{MAX_RETRIES}: {e}"
            )

        # Handle Retries
        if attempt < MAX_RETRIES - 1:
            print("    -> [*] Waiting 5 seconds before retrying...")
            time.sleep(5)

    # 6. Graceful Failure (If all 3 attempts fail)
    print("    -> [!] Max retries reached. Skipping analysis for this job.")

    # Return a safely formatted fallback dictionary so the Google Sheets insertion doesn't crash
    return {
        "score": 0,
        "dimension_scores": {
            "hard_skills_match": 0,
            "experience_level_alignment": 0,
            "project_impact_alignment": 0,
            "responsibility_complexity_match": 0,
            "education_certifications": 0,
            "keywords_ats_compatibility": 0,
        },
        "missing_critical_skills": ["Analysis failed due to API timeout/error."],
        "matching_strengths": [],
        "improvements": "N/A — API connection failed.",
    }
