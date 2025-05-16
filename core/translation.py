import os
import json
from .constants import ASSETS_DIR_NAME, LANGS_DIR_NAME # Import from sibling constants.py

translations = {}
current_language = "en" # Default language at startup

def get_langs_dir():

    script_dir = os.path.dirname(os.path.abspath(__file__)) # core directory
    project_root_from_core = os.path.dirname(script_dir)
    return os.path.join(project_root_from_core, ASSETS_DIR_NAME, LANGS_DIR_NAME)

def load_translations(lang_code):

    global translations, current_language
    current_language = lang_code
    langs_dir = get_langs_dir()
    translations_path = os.path.join(langs_dir, f"{lang_code}.json")
    default_translations_path = os.path.join(langs_dir, "en.json")

    try:
        with open(translations_path, 'r', encoding='utf-8') as f:
            translations = json.load(f)
    except FileNotFoundError:
        print(f"Warning: Language file '{translations_path}' not found. Falling back to English.")
        try:
            with open(default_translations_path, 'r', encoding='utf-8') as f:
                translations = json.load(f)
            current_language = "en"
        except FileNotFoundError:
            print(f"Error: Default English language file '{default_translations_path}' not found.")
            translations = {}
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{translations_path}'. Trying English.")
        try:
            with open(default_translations_path, 'r', encoding='utf-8') as f:
                translations = json.load(f)
            current_language = "en"
        except Exception as e:
             print(f"CRITICAL: Failed to load any language files: {e}")
             translations = {}

def tr(key, *args, **kwargs):

    text = translations.get(key, f"_{key}_") # Return _key_ if not found for easier spotting
    try:
        if args and kwargs: return text.format(*args, **kwargs)
        if args: return text.format(*args)
        if kwargs: return text.format(**kwargs)
        return text
    except (KeyError, IndexError, TypeError):
        return f"_{key}_(err)" # Indicate formatting error
