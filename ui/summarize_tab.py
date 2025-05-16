from PyQt5.QtWidgets import QPushButton, QLabel, QPlainTextEdit, QHBoxLayout, QFileDialog, QMessageBox
from PyQt5.QtGui import QFont
from ui.base_tab import BaseFeatureTab
from core.translation import tr

class SummarizeCodeTab(BaseFeatureTab):

    def _init_specific_ui_elements(self):

        self.attach_button = QPushButton()
        self.source_code_label_widget = QLabel()
        self.input_code = QPlainTextEdit()
        self.summarize_button = QPushButton()

        self.attach_button._translatable_key = "attach_file_btn"
        self.summarize_button._translatable_key = "summarize_btn"
        self.source_code_label_widget._translatable_key = "source_code_label"
        self.input_code._translatable_placeholder_key = "code_input_placeholder"

        self.input_code.setFont(QFont("Consolas", 10))
        self.input_code.setLineWrapMode(QPlainTextEdit.NoWrap)

        self._retranslate_specific_ui()

    def _setup_layout_structure(self):

        hbox_attach = QHBoxLayout()
        hbox_attach.addWidget(self.attach_button)
        hbox_attach.addStretch(1)
        self.layout.addLayout(hbox_attach)

        self.layout.addWidget(self.source_code_label_widget)
        self.layout.addWidget(self.input_code, 1)
        self.layout.addWidget(self.summarize_button)

    def _connect_signals(self):

        self.attach_button.clicked.connect(self._attach_file)
        self.summarize_button.clicked.connect(self._summarize_code)

    def _retranslate_specific_ui(self):

        self.attach_button.setText(tr(self.attach_button._translatable_key))
        self.source_code_label_widget.setText(tr(self.source_code_label_widget._translatable_key))
        self.input_code.setPlaceholderText(tr(self.input_code._translatable_placeholder_key))
        self.summarize_button.setText(tr(self.summarize_button._translatable_key))

    def retranslate_ui(self):

        super().retranslate_ui()
        self._retranslate_specific_ui()

    def _attach_file(self):

        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, tr("attach_file_btn"), "",
            "Python Files (*.py);;Text Files (*.txt);;All Files (*)",
            options=options
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.input_code.setPlainText(f.read())
            except Exception as e:
                QMessageBox.critical(self, tr("error_title"), tr("file_not_found_err", str(e)))

    def _summarize_code(self):

        code = self.input_code.toPlainText().strip()
        if not code:
            QMessageBox.warning(self, tr("error_title"), tr("empty_input_err"))
            return

        prompt = (
            "You are an expert programming assistant. Your task is to summarize the "
            "following code. The summary should focus on the main functionality, its "
            "most important parts, and how it works in general. The response should "
            "be in Markdown format. Do not include the original code in your response, "
            "only the summary.\n\n"
            "Code:\n```\n"
            f"{code}\n"
            "```\n\n"
            "Summary (Markdown):"
        )
        self.store_last_prompt(prompt, tr("summarize_tab"))
        self.main_window.start_gemini_task(prompt, self.result_display, tr("summarize_tab"))
