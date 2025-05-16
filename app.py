import sys
import os
import json
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSettings

from ui.main_window import MainWindow # MainWindow now takes version and developer
from core.translation import load_translations
from core.constants import DEFAULT_MODEL, SETTINGS_FILE_NAME, LANGS_DIR_NAME, ASSETS_DIR_NAME

APP_VERSION_CONST = "1.0"
APP_DEVELOPER_CONST = "Mohammed Alhaji"

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

LANGS_DIR_APP = os.path.join(PROJECT_ROOT, ASSETS_DIR_NAME, LANGS_DIR_NAME)

def create_default_lang_files_if_missing():

    minimal_ar = {
        "app_title": "AI Helper", "status_ready": "جاهز",
        "api_rate_limit_exceeded": "Rate limit.", "api_invalid_argument":"Invalid input."

    }
    minimal_en = {
        "app_title": "AI Helper", "status_ready": "Ready",
        "api_rate_limit_exceeded": "Rate limit.", "api_invalid_argument":"Invalid input."
    }

    os.makedirs(LANGS_DIR_APP, exist_ok=True)
    for lang_code, content in [("ar", minimal_ar), ("en", minimal_en)]:
        lang_file_path = os.path.join(LANGS_DIR_APP, f"{lang_code}.json")
        if not os.path.exists(lang_file_path):
            try:
                with open(lang_file_path, 'w', encoding='utf-8') as f:
                    json.dump(content, f, ensure_ascii=False, indent=4)
                print(f"Created minimal default language file: {lang_file_path}")
            except IOError as e:
                print(f"Could not create default language file {lang_file_path}: {e}")

def main():

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    os.makedirs(os.path.join(PROJECT_ROOT, "docs"), exist_ok=True)
    os.makedirs(os.path.join(PROJECT_ROOT, "logs"), exist_ok=True)
    os.makedirs(os.path.join(PROJECT_ROOT, ASSETS_DIR_NAME), exist_ok=True) # Ensure assets dir
    create_default_lang_files_if_missing()

    settings_file_path_app = os.path.join(PROJECT_ROOT, SETTINGS_FILE_NAME)
    settings = QSettings(settings_file_path_app, QSettings.IniFormat)

    if not settings.contains("language"):
        settings.setValue("language", "en") # Default to English
    if not settings.contains("api_key"):
        settings.setValue("api_key", "")
    if not settings.contains("gemini_model"):
        settings.setValue("gemini_model", DEFAULT_MODEL) # From core.constants

    initial_lang = settings.value("language", "en")
    load_translations(initial_lang)

    main_window = MainWindow(
        app_version_str=APP_VERSION_CONST,
        developer_name_str=APP_DEVELOPER_CONST
    )
    main_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
