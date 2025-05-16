import os
from PyQt5.QtWidgets import (QPushButton, QLabel, QPlainTextEdit, QHBoxLayout, QFormLayout, QFileDialog, QMessageBox, QComboBox)
from PyQt5.QtGui import QFont
from ui.base_tab import BaseFeatureTab
from core.translation import tr

PROGRAMMING_LANGUAGES = [
    "Python", "JavaScript", "Java", "C++", "C#", "Ruby", "Go", "Swift", "Kotlin",
    "PHP", "TypeScript", "Rust", "Scala", "Perl", "Lua", "SQL", "HTML", "CSS", "Shell"
]

class TranslateCodeTab(BaseFeatureTab):

    def _init_specific_ui_elements(self):
        self.attach_button = QPushButton(); self.source_code_label_widget = QLabel()
        self.input_code = QPlainTextEdit(); self.source_lang_label = QLabel()
        self.source_lang_combo = QComboBox(); self.target_lang_label = QLabel()
        self.target_lang_combo = QComboBox(); self.translate_button = QPushButton()
        self.attach_button._translatable_key = "attach_file_btn"
        self.source_code_label_widget._translatable_key = "source_code_label"
        self.input_code._translatable_placeholder_key = "code_input_placeholder"
        self.source_lang_label._translatable_key = "source_lang_label"
        self.target_lang_label._translatable_key = "target_lang_label"
        self.translate_button._translatable_key = "translate_code_btn"
        self.input_code.setFont(QFont("Consolas", 10)); self.input_code.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.source_lang_combo.addItems(PROGRAMMING_LANGUAGES); self.source_lang_combo.setCurrentText("Python")
        self.target_lang_combo.addItems(PROGRAMMING_LANGUAGES); self.target_lang_combo.setCurrentText("JavaScript")
        self._retranslate_specific_ui()
    def _setup_layout_structure(self):
        hbox_attach = QHBoxLayout(); hbox_attach.addWidget(self.attach_button); hbox_attach.addStretch(1)
        self.layout.addLayout(hbox_attach); self.layout.addWidget(self.source_code_label_widget)
        self.layout.addWidget(self.input_code, 1); form_layout = QFormLayout()
        form_layout.addRow(self.source_lang_label, self.source_lang_combo)
        form_layout.addRow(self.target_lang_label, self.target_lang_combo)
        self.layout.addLayout(form_layout); self.layout.addWidget(self.translate_button)
    def _connect_signals(self):
        self.attach_button.clicked.connect(self._attach_file)
        self.translate_button.clicked.connect(self._translate_code)
    def _retranslate_specific_ui(self):
        self.attach_button.setText(tr(self.attach_button._translatable_key))
        self.source_code_label_widget.setText(tr(self.source_code_label_widget._translatable_key))
        self.input_code.setPlaceholderText(tr(self.input_code._translatable_placeholder_key))
        self.source_lang_label.setText(tr(self.source_lang_label._translatable_key))
        self.target_lang_label.setText(tr(self.target_lang_label._translatable_key))
        self.translate_button.setText(tr(self.translate_button._translatable_key))
    def retranslate_ui(self): super().retranslate_ui(); self._retranslate_specific_ui()
    def _attach_file(self):
        options = QFileDialog.Options(); file_path, _ = QFileDialog.getOpenFileName(self, tr("attach_file_btn"), "", "All Files (*)", options=options)
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f: self.input_code.setPlainText(f.read())
                _, ext = os.path.splitext(file_path)
                lang_map = { ".py": "Python", ".js": "JavaScript", ".java": "Java", ".cpp": "C++", ".cs": "C#", ".rb": "Ruby", ".go": "Go", ".swift": "Swift", ".kt": "Kotlin", ".php": "PHP", ".ts": "TypeScript", ".rs": "Rust", ".scala": "Scala", ".pl": "Perl", ".lua": "Lua", ".sql": "SQL", ".html": "HTML", ".css": "CSS", ".sh": "Shell", ".bash": "Shell"}
                guessed_lang = lang_map.get(ext.lower())
                if guessed_lang and guessed_lang in PROGRAMMING_LANGUAGES: self.source_lang_combo.setCurrentText(guessed_lang)
            except Exception as e: QMessageBox.critical(self, tr("error_title"), tr("file_not_found_err", str(e)))
    def _translate_code(self):
        code = self.input_code.toPlainText().strip(); source_lang = self.source_lang_combo.currentText(); target_lang = self.target_lang_combo.currentText()
        if not code or not source_lang or not target_lang: QMessageBox.warning(self, tr("error_title"), tr("empty_input_err")); return
        if source_lang == target_lang: QMessageBox.information(self, tr("translate_code_tab"), "Source and target languages are the same."); return
        prompt = (
            f"You are an expert code translator. Your task is to translate the following "
            f"code snippet from {source_lang} to {target_lang}. Provide only the "
            f"translated code, enclosed in a ```{target_lang.lower()} ... ``` fenced "
            f"code block (Markdown). Do not include any additional explanations or text "
            f"before or after the code block. Focus on a direct and accurate translation, "
            f"maintaining the original logic and functionality as closely as possible.\n\n"
            f"Original {source_lang} code:\n```{source_lang.lower()}\n{code}\n```\n\n"
            f"Translated {target_lang} code (within a Markdown code block for {target_lang.lower()}):\n"
        )
        self.store_last_prompt(prompt, tr("translate_code_tab"))
        self.main_window.start_gemini_task(prompt, self.result_display, tr("translate_code_tab"))
