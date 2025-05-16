from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QLabel,
                             QPushButton, QHBoxLayout, QFileDialog, QMessageBox, QStyle)
from PyQt5.QtWidgets import QApplication
from core.translation import tr

class BaseFeatureTab(QWidget):

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.layout = QVBoxLayout(self)

        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)

        self.last_prompt = None
        self.last_tab_name_for_log = ""

        self._init_specific_ui_elements()
        self._setup_layout_structure()
        self._populate_common_layout_elements()
        self._connect_signals()
        self._connect_common_signals()

    def _init_specific_ui_elements(self):

        pass

    def _setup_layout_structure(self):

        pass

    def _populate_common_layout_elements(self):

        self.result_label_widget = QLabel(tr("result_label"))
        self.result_label_widget._translatable_key = "result_label"

        self.copy_btn = QPushButton(tr("copy_result_btn"))
        self.copy_btn._translatable_key = "copy_result_btn"
        self.copy_btn.setIcon(self.style().standardIcon(QStyle.SP_FileLinkIcon))

        self.save_btn = QPushButton(tr("save_result_btn"))
        self.save_btn._translatable_key = "save_result_btn"
        self.save_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))

        self.regenerate_btn = QPushButton(tr("regenerate_btn"))
        self.regenerate_btn._translatable_key = "regenerate_btn"
        self.regenerate_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))

        self.layout.addWidget(self.result_label_widget)
        self.layout.addWidget(self.result_display, 1) # Stretch factor for result display

        result_buttons_layout = QHBoxLayout()
        result_buttons_layout.addStretch()
        result_buttons_layout.addWidget(self.copy_btn)
        result_buttons_layout.addWidget(self.save_btn)
        result_buttons_layout.addWidget(self.regenerate_btn)
        self.layout.addLayout(result_buttons_layout)

    def _connect_signals(self):

        pass

    def _connect_common_signals(self):

        self.copy_btn.clicked.connect(self._copy_result)
        self.save_btn.clicked.connect(self._save_result)
        self.regenerate_btn.clicked.connect(self._regenerate_result)

    def store_last_prompt(self, prompt, tab_name_for_log):

        self.last_prompt = prompt
        self.last_tab_name_for_log = tab_name_for_log

    def _regenerate_result(self):

        if self.last_prompt:
            self.main_window.start_gemini_task(
                self.last_prompt,
                self.result_display,
                self.last_tab_name_for_log
            )
        else:
            QMessageBox.information(self, tr("regenerate_btn"), tr("status_no_previous_request"))
            self.main_window.statusBar().showMessage(tr("status_no_previous_request"), 3000)

    def retranslate_ui(self):

        self.result_label_widget.setText(tr(self.result_label_widget._translatable_key))
        self.copy_btn.setText(tr(self.copy_btn._translatable_key))
        self.save_btn.setText(tr(self.save_btn._translatable_key))
        self.regenerate_btn.setText(tr(self.regenerate_btn._translatable_key))

    def _copy_result(self):

        QApplication.clipboard().setText(self.result_display.toPlainText())
        self.main_window.statusBar().showMessage(tr("result_copied_clipboard"), 2000)

    def _save_result(self):

        content = self.result_display.toPlainText()
        if not content.strip():
            QMessageBox.information(self, tr("save_result_btn"), tr("save_result_no_content"))
            return

        options = QFileDialog.Options()
        default_filename = "gemini_result.md"
        if "```python" in content or ("def " in content and "import " in content):
            default_filename = "gemini_code.py"
        elif "```" not in content:
            default_filename = "gemini_text.txt"

        file_path, _ = QFileDialog.getSaveFileName(
            self, tr("save_result_btn"), default_filename,
            "Markdown Files (*.md);;Python Files (*.py);;Text Files (*.txt);;All Files (*)",
            options=options
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.main_window.statusBar().showMessage(tr("result_saved_to", file_path), 3000)
            except Exception as e:
                QMessageBox.critical(self, tr("error_title"), tr("save_result_error", str(e)))
