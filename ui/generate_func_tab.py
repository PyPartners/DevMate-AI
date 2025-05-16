from PyQt5.QtWidgets import QLabel, QTextEdit, QLineEdit, QPushButton, QFormLayout, QMessageBox
from PyQt5.QtGui import QFont
from ui.base_tab import BaseFeatureTab
from core.translation import tr

class GenerateFunctionTab(BaseFeatureTab):

    def _init_specific_ui_elements(self):
        self.func_desc_label = QLabel(); self.func_desc_input = QTextEdit()
        self.optional_libs_label = QLabel(); self.optional_libs_input = QLineEdit()
        self.generate_button = QPushButton()
        self.func_desc_label._translatable_key = "func_desc_label"
        self.optional_libs_label._translatable_key = "optional_libs_label"
        self.generate_button._translatable_key = "generate_btn"
        self.func_desc_input.setFont(QFont("Arial", 10)); self.func_desc_input.setMinimumHeight(80)
        self._retranslate_specific_ui()
    def _setup_layout_structure(self):
        form_layout = QFormLayout()
        form_layout.addRow(self.func_desc_label, self.func_desc_input)
        form_layout.addRow(self.optional_libs_label, self.optional_libs_input)
        self.layout.addLayout(form_layout); self.layout.addWidget(self.generate_button)
    def _connect_signals(self): self.generate_button.clicked.connect(self._generate_function)
    def _retranslate_specific_ui(self):
        self.func_desc_label.setText(tr(self.func_desc_label._translatable_key))
        self.optional_libs_label.setText(tr(self.optional_libs_label._translatable_key))
        self.generate_button.setText(tr(self.generate_button._translatable_key))
    def retranslate_ui(self): super().retranslate_ui(); self._retranslate_specific_ui()
    def _generate_function(self):
        description = self.func_desc_input.toPlainText().strip()
        libraries = self.optional_libs_input.text().strip()
        if not description: QMessageBox.warning(self, tr("error_title"), tr("empty_input_err")); return
        prompt_lines = [
            "You are an expert programming assistant. Your task is to create a Python ",
            "function based on the following description. Provide only the code, ",
            "enclosed in a ```python ... ``` fenced code block (Markdown). Do not ",
            "include any additional explanations or text before or after the code block, ",
            "unless explicitly requested in the description. If libraries are specified, use them.",
            f"\nDescription: {description}"
        ]
        if libraries: prompt_lines.append(f"Required/Suggested libraries: {libraries}")
        prompt_lines.append("\nRequested code (Python only, within a Markdown code block):\n")
        prompt = "\n".join(prompt_lines)
        self.store_last_prompt(prompt, tr("generate_func_tab"))
        self.main_window.start_gemini_task(prompt, self.result_display, tr("generate_func_tab"))
