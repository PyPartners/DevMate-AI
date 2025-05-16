import os
from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QComboBox, QPushButton, QMessageBox
from PyQt5.QtCore import QSettings, pyqtSignal
from .translation import tr, get_langs_dir
from .constants import AVAILABLE_MODELS, DEFAULT_MODEL, SETTINGS_FILE_NAME

class SettingsDialog(QDialog):

    settings_changed_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.settings_file_path = parent.settings_file_path if parent and hasattr(parent, 'settings_file_path') else SETTINGS_FILE_NAME
        self.settings = QSettings(self.settings_file_path, QSettings.IniFormat)

        self._init_ui()
        self._load_settings()

    def _init_ui(self):

        self.setWindowTitle(tr("settings_title"))
        self.setMinimumWidth(450)
        layout = QFormLayout(self)

        self.api_key_input = QLineEdit(self)
        layout.addRow(tr("api_key_label"), self.api_key_input)

        self.language_combo = QComboBox(self)
        langs_dir = get_langs_dir()
        available_lang_files = []
        if os.path.exists(langs_dir) and os.path.isdir(langs_dir):
             available_lang_files = [f.split('.')[0] for f in os.listdir(langs_dir) if f.endswith(".json")]

        self.lang_map = {}
        for lang_code in available_lang_files:
            display_name = f"{lang_code.upper()} ({lang_code})"
            if lang_code == "ar": display_name = f"العربية ({lang_code})"
            elif lang_code == "en": display_name = f"English ({lang_code})"
            self.language_combo.addItem(display_name, lang_code)
            self.lang_map[display_name] = lang_code
        layout.addRow(tr("language_label"), self.language_combo)

        self.model_combo = QComboBox(self)
        self.model_combo.addItems(AVAILABLE_MODELS)
        layout.addRow(tr("model_label"), self.model_combo)

        self.save_button = QPushButton(tr("save_settings_btn"), self)
        self.save_button.clicked.connect(self._save_settings)
        layout.addRow(self.save_button)

    def _load_settings(self):

        self.api_key_input.setText(self.settings.value("api_key", ""))

        saved_lang_code = self.settings.value("language", "en")
        index = self.language_combo.findData(saved_lang_code)
        if index != -1:
            self.language_combo.setCurrentIndex(index)
        elif self.language_combo.count() > 0:
             english_index = self.language_combo.findData("en")
             self.language_combo.setCurrentIndex(english_index if english_index != -1 else 0)

        saved_model = self.settings.value("gemini_model", DEFAULT_MODEL)
        if saved_model in AVAILABLE_MODELS:
            self.model_combo.setCurrentText(saved_model)
        else:
            if DEFAULT_MODEL in AVAILABLE_MODELS:
                self.model_combo.setCurrentText(DEFAULT_MODEL)
            elif self.model_combo.count() > 0:
                self.model_combo.setCurrentIndex(0)

    def _save_settings(self):

        self.settings.setValue("api_key", self.api_key_input.text())

        lang_code = self.language_combo.currentData() # Get lang_code from userData
        if not lang_code and self.language_combo.count() > 0: # Fallback if currentData is None
            selected_display_lang = self.language_combo.currentText()
            lang_code = self.lang_map.get(selected_display_lang, "en")
        elif not lang_code: 
            lang_code = "en"
        self.settings.setValue("language", lang_code)

        self.settings.setValue("gemini_model", self.model_combo.currentText())

        QMessageBox.information(
            self, tr("settings_title"),
            tr("settings_saved_relaunch_lang") + "\n" + tr("settings_saved_model_applied")
        )
        self.settings_changed_signal.emit()
        self.accept()
