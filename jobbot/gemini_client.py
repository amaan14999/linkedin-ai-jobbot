import json
import os
from google import genai
from google.genai import types


def analyze_job_match(
    resume_text: str, job_description: str, min_score: int, model_name: str
) -> dict:
    """
    Sends the resume and JD to Gemini and returns a parsed JSON dictionary.
    """

    try:
        client = genai.Client()
    except Exception as e:
        print(f"[!] Failed to initialize Gemini Client. Check your API key. Error: {e}")
        return {"score": 0, "improvements": "API Client setup failed."}

    # Read the prompt template from the root folder
    try:
        prompt_path = os.path.join(os.getcwd(), "prompts.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        print("[!] prompts.txt not found. Please create it in the root directory.")
        return {"score": 0, "improvements": "Prompt file missing."}

    # 3. Inject the actual resume and JD into the prompt
    final_prompt = prompt_template.format(
        resume=resume_text, min_score=min_score, job_description=job_description
    )

    # 4. Call the Gemini API
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=final_prompt,
            config=types.GenerateContentConfig(
                # Force pure JSON output so we can parse it reliably
                response_mime_type="application/json",
                # Low temperature (0.2) forces analytical, consistent scoring
                temperature=0.2,
            ),
        )

        # 5. Parse and return the JSON dictionary
        result_dict = json.loads(response.text)
        return result_dict

    except json.JSONDecodeError:
        print("[!] Gemini returned invalid JSON instead of the requested format.")
        return {"score": 0, "improvements": "Failed to parse AI response."}
    except Exception as e:
        print(f"[!] Error communicating with Gemini API: {e}")
        return {"score": 0, "improvements": "API connection failed."}
