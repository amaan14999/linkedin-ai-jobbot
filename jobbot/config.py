import yaml
import os


def load_config(config_path: str = "config.yaml") -> dict:
    """Reads the YAML file and supplies safe default values."""
    full_path = os.path.join(os.getcwd(), config_path)

    try:
        with open(full_path, "r", encoding="utf-8") as file:
            raw_data = yaml.safe_load(file) or {}
    except FileNotFoundError:
        print(f"[!] {config_path} not found. Using default settings.")
        raw_data = {}

    li_data = raw_data.get("linkedin", {})
    app_data = raw_data.get("app", {})

    return {
        "linkedin": {
            "keywords": li_data.get("keywords", "software engineer"),
            "location": li_data.get("location", "Bengaluru"),
            "distance": li_data.get("distance", 40),
            "f_WT": li_data.get("f_WT", ""),
            "experience_levels": li_data.get("experience_levels", "2"),
            "easy_apply": li_data.get("easy_apply", False),
            "company_ids": li_data.get("company_ids", []),
            "results_wanted": li_data.get("results_wanted", 100),
            "filter_out_companies": li_data.get("filter_out_companies", []),
        },
        "app": {
            "min_ai_score": app_data.get("min_ai_score", 6),
            "gemini_model": app_data.get("gemini_model", "gemini-3-flash"),
        },
    }
