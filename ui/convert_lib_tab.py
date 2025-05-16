from PyQt5.QtWidgets import (QPushButton, QLabel, QPlainTextEdit, QHBoxLayout, QLineEdit, QFormLayout, QFileDialog, QMessageBox)
from PyQt5.QtGui import QFont
from ui.base_tab import BaseFeatureTab
from core.translation import tr

class ConvertLibraryTab(BaseFeatureTab):

    def _init_specific_ui_elements(self):
        self.attach_button = QPushButton(); self.source_code_label_widget = QLabel()
        self.input_code = QPlainTextEdit(); self.source_lib_label = QLabel()
        self.source_lib_input = QLineEdit(); self.target_lib_label = QLabel()
        self.target_lib_input = QLineEdit(); self.convert_button = QPushButton()
        self.attach_button._translatable_key = "attach_file_btn"
        self.source_code_label_widget._translatable_key = "source_code_label"
        self.input_code._translatable_placeholder_key = "code_input_placeholder"
        self.source_lib_label._translatable_key = "source_lib_label"
        self.source_lib_input._translatable_placeholder_key = "source_lib_placeholder"
        self.target_lib_label._translatable_key = "target_lib_label"
        self.target_lib_input._translatable_placeholder_key = "target_lib_placeholder"
        self.convert_button._translatable_key = "convert_btn"
        self.input_code.setFont(QFont("Consolas", 10)); self.input_code.setLineWrapMode(QPlainTextEdit.NoWrap)
        self._retranslate_specific_ui()
    def _setup_layout_structure(self):
        hbox_attach = QHBoxLayout(); hbox_attach.addWidget(self.attach_button); hbox_attach.addStretch(1)
        self.layout.addLayout(hbox_attach); self.layout.addWidget(self.source_code_label_widget)
        self.layout.addWidget(self.input_code, 1); form_layout = QFormLayout()
        form_layout.addRow(self.source_lib_label, self.source_lib_input)
        form_layout.addRow(self.target_lib_label, self.target_lib_input)
        self.layout.addLayout(form_layout); self.layout.addWidget(self.convert_button)
    def _connect_signals(self):
        self.attach_button.clicked.connect(self._attach_file)
        self.convert_button.clicked.connect(self._convert_library)
    def _retranslate_specific_ui(self):
        self.attach_button.setText(tr(self.attach_button._translatable_key))
        self.source_code_label_widget.setText(tr(self.source_code_label_widget._translatable_key))
        self.input_code.setPlaceholderText(tr(self.input_code._translatable_placeholder_key))
        self.source_lib_label.setText(tr(self.source_lib_label._translatable_key))
        self.source_lib_input.setPlaceholderText(tr(self.source_lib_input._translatable_placeholder_key))
        self.target_lib_label.setText(tr(self.target_lib_label._translatable_key))
        self.target_lib_input.setPlaceholderText(tr(self.target_lib_input._translatable_placeholder_key))
        self.convert_button.setText(tr(self.convert_button._translatable_key))
    def retranslate_ui(self): super().retranslate_ui(); self._retranslate_specific_ui()
    def _attach_file(self):
        options = QFileDialog.Options(); file_path, _ = QFileDialog.getOpenFileName(self, tr("attach_file_btn"), "", "Python Files (*.py);;Text Files (*.txt);;All Files (*)", options=options)
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f: self.input_code.setPlainText(f.read())
            except Exception as e: QMessageBox.critical(self, tr("error_title"), tr("file_not_found_err", str(e)))
    def _convert_library(self):
        code = self.input_code.toPlainText().strip()
        source_lib = self.source_lib_input.text().strip(); target_lib = self.target_lib_input.text().strip()
        if not code or not source_lib or not target_lib: QMessageBox.warning(self, tr("error_title"), tr("empty_input_err")); return
        prompt = (
            f"You are an expert in converting Python code between different libraries. "
            f"Your task is to convert the following code from using the '{source_lib}' "
            f"library to using the '{target_lib}' library. Provide only the converted "
            f"code, enclosed in a ```python ... ``` fenced code block (Markdown). Do not "
            f"include any additional explanations or text before or after the code block, "
            f"unless essential to clarify a critical point. Try to maintain the same "
            f"functionality as much as possible.\n\n"
            f"Original code (using {source_lib}):\n```python\n{code}\n```\n\n"
            f"Requested code (using {target_lib}, within a Markdown code block):\n"
        )
        self.store_last_prompt(prompt, tr("convert_lib_tab"))
        self.main_window.start_gemini_task(prompt, self.result_display, tr("convert_lib_tab"))
