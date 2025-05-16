import os
import datetime
import markdown2
import textwrap
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTabWidget,
                             QLabel, QTextEdit, QMessageBox, QSplitter, QAction)
from PyQt5.QtGui import QTextCursor, QIcon
from PyQt5.QtCore import QSettings, QThread, Qt

from core.translation import tr, load_translations, current_language as translation_current_language
from core.gemini_worker import GeminiWorker
from core.settings_dialog import SettingsDialog
from core.constants import (DEFAULT_MODEL, SETTINGS_FILE_NAME, APP_NAME_KEY, APP_ICON_NAME,
                            ASSETS_DIR_NAME, DOCS_DIR_NAME, LOGS_DIR_NAME, CHAT_HISTORY_FILE_NAME)

from ui.summarize_tab import SummarizeCodeTab
from ui.generate_func_tab import GenerateFunctionTab
from ui.debug_code_tab import DebugCodeTab
from ui.convert_lib_tab import ConvertLibraryTab
from ui.translate_code_tab import TranslateCodeTab

class MainWindow(QMainWindow):
    # Main application window.
    def __init__(self, app_version_str, developer_name_str):
        super().__init__()
        self.app_version = app_version_str
        self.app_developer = developer_name_str
        
        ui_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(ui_dir)
        
        self.assets_dir = os.path.join(self.project_root, ASSETS_DIR_NAME)
        self.app_icon_path = os.path.join(self.assets_dir, APP_ICON_NAME)
        self.docs_dir = os.path.join(self.project_root, DOCS_DIR_NAME)
        self.logs_dir = os.path.join(self.project_root, LOGS_DIR_NAME)
        self.chat_history_file = os.path.join(self.logs_dir, CHAT_HISTORY_FILE_NAME)
        self.settings_file_path = os.path.join(self.project_root, SETTINGS_FILE_NAME)

        self.settings = QSettings(self.settings_file_path, QSettings.IniFormat)
        self.docs_content_cache = ""
        self.current_model_name = DEFAULT_MODEL
        self.thread = None
        self.worker = None
        
        self._load_initial_language_and_translations()
        self._init_folders()
        self._load_docs_on_first_run()
        self._init_ui()
        self._load_api_key_and_model()

    def _load_initial_language_and_translations(self):
        # Loads interface language based on settings.
        lang_code = self.settings.value("language", "en")
        load_translations(lang_code)

    def _init_folders(self):
        # Creates necessary application folders if they don't exist.
        os.makedirs(self.docs_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.assets_dir, exist_ok=True)

    def _retranslate_ui(self):
        # Updates UI texts when language changes.
        self.setWindowTitle(tr(APP_NAME_KEY))
        if os.path.exists(self.app_icon_path):
            self.setWindowIcon(QIcon(self.app_icon_path))
            
        self.file_menu.setTitle(tr("file_menu"))
        self.settings_action.setText(tr("settings_menu"))
        self.exit_action.setText(tr("exit_menu"))
        self.help_menu.setTitle(tr("help_menu"))
        self.about_action.setText(tr("about_menu"))

        tab_widgets_map = {
            self.summarize_tab_widget: "summarize_tab",
            self.generate_func_tab_widget: "generate_func_tab",
            self.debug_code_tab_widget: "debug_code_tab",
            self.convert_lib_tab_widget: "convert_lib_tab",
            self.translate_code_tab_widget: "translate_code_tab"
        }
        for widget, key in tab_widgets_map.items():
            index = self.tabs.indexOf(widget)
            if index != -1:
                self.tabs.setTabText(index, tr(key))
            if hasattr(widget, 'retranslate_ui'):
                 widget.retranslate_ui()
        
        self.chat_history_display_label.setText(tr("chat_history_label"))
        current_status = self.statusBar().currentMessage()
        if not any(error_key in current_status for error_key in [
            tr("status_api_key_missing"), 
            tr("status_model_not_selected"), 
            tr("status_error")]
        ):
            self.statusBar().showMessage(tr("status_ready"))

    def _apply_dark_theme(self):
        # Applies a dark theme stylesheet to the application.
        stylesheet = textwrap.dedent("""
            QMainWindow, QDialog { background-color: #2E2E2E; }
            QTabWidget::pane { border: 1px solid #444; background-color: #3C3C3C; }
            QTabBar::tab {
                background: #555; color: #FFF; padding: 10px;
                border: 1px solid #444; border-bottom: none; margin-right: 2px;
            }
            QTabBar::tab:selected { background: #3C3C3C; border-bottom: 1px solid #3C3C3C; }
            QTabBar::tab:hover { background: #666; }
            QWidget { background-color: #3C3C3C; color: #F0F0F0; font-size: 10pt; }
            QLabel { color: #E0E0E0; font-size: 10pt; }
            QLineEdit, QTextEdit, QPlainTextEdit {
                background-color: #252525; color: #F0F0F0; border: 1px solid #555;
                padding: 5px; font-family: "Consolas", "Monospace", "Courier New"; font-size: 10pt;
            }
            QPushButton {
                background-color: #5C8DDE; color: white; border: 1px solid #4A7AC4;
                padding: 8px 15px; border-radius: 4px; font-size: 10pt;
            }
            QPushButton:hover { background-color: #4A7AC4; }
            QPushButton:pressed { background-color: #3A6AB4; }
            QMessageBox { background-color: #3C3C3C; }
            QMessageBox QLabel { color: #F0F0F0; }
            QSplitter::handle { background-color: #555; }
            QSplitter::handle:hover { background-color: #666; }
            QSplitter::handle:pressed { background-color: #444; }
            QScrollBar:vertical {
                border: 1px solid #2E2E2E; background: #3C3C3C; width: 15px;
                margin: 15px 0 15px 0;
            }
            QScrollBar::handle:vertical { background: #555; min-height: 20px; border-radius: 7px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none; background: none; height: 15px;
                subcontrol-position: top; subcontrol-origin: margin;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical { background: none; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
            QComboBox {
                border: 1px solid #555; padding: 5px; background-color: #252525; min-width: 6em;
            }
            QComboBox:editable { background: #252525; }
            QComboBox:!editable, QComboBox::drop-down:editable { background: #5C8DDE; }
            QComboBox:!editable:on, QComboBox::drop-down:editable:on { background: #4A7AC4; }
            QComboBox QAbstractItemView {
                border: 1px solid #555; selection-background-color: #5C8DDE;
                background-color: #252525; color: #F0F0F0;
            }
            QMenu { background-color: #3C3C3C; border: 1px solid #555; }
            QMenu::item { padding: 5px 20px 5px 20px; }
            QMenu::item:selected { background-color: #5C8DDE; }
        """)
        self.setStyleSheet(stylesheet)

    def _init_ui(self):
        # Initializes the main UI components.
        self.setWindowTitle(tr(APP_NAME_KEY))
        if os.path.exists(self.app_icon_path):
            self.setWindowIcon(QIcon(self.app_icon_path))
        else:
            print(f"Warning: App icon '{APP_ICON_NAME}' not found in '{self.assets_dir}'.")
            
        self.setGeometry(100, 100, 1000, 700)
        self._apply_dark_theme()
        
        self._create_menus()

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)

        self._create_tabs()
        splitter.addWidget(self.tabs_container)

        self._create_chat_history_area()
        splitter.addWidget(self.chat_history_widget)
        
        splitter.setSizes([int(self.height() * 0.65), int(self.height() * 0.35)])
        self.statusBar().showMessage(tr("status_ready"))

    # ... (بقية دوال MainWindow تبقى كما هي) ...
    def _create_menus(self):
        # Creates the main menu bar and its actions.
        menubar = self.menuBar()
        self.file_menu = menubar.addMenu(tr("file_menu"))
        
        self.settings_action = QAction(tr("settings_menu"), self)
        self.settings_action.triggered.connect(self._open_settings)
        self.file_menu.addAction(self.settings_action)
        
        self.file_menu.addSeparator()
        
        self.exit_action = QAction(tr("exit_menu"), self)
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)

        self.help_menu = menubar.addMenu(tr("help_menu"))
        self.about_action = QAction(tr("about_menu"), self)
        self.about_action.triggered.connect(self._show_about_dialog)
        self.help_menu.addAction(self.about_action)

    def _create_tabs(self):
        # Creates the tab widget and individual feature tabs.
        self.tabs_container = QWidget()
        tabs_layout = QVBoxLayout(self.tabs_container)
        tabs_layout.setContentsMargins(0,0,0,0)
        self.tabs = QTabWidget()
        tabs_layout.addWidget(self.tabs)

        self.summarize_tab_widget = SummarizeCodeTab(self)
        self.generate_func_tab_widget = GenerateFunctionTab(self)
        self.debug_code_tab_widget = DebugCodeTab(self)
        self.convert_lib_tab_widget = ConvertLibraryTab(self)
        self.translate_code_tab_widget = TranslateCodeTab(self)

        self.tabs.addTab(self.summarize_tab_widget, tr("summarize_tab"))
        self.tabs.addTab(self.generate_func_tab_widget, tr("generate_func_tab"))
        self.tabs.addTab(self.debug_code_tab_widget, tr("debug_code_tab"))
        self.tabs.addTab(self.convert_lib_tab_widget, tr("convert_lib_tab"))
        self.tabs.addTab(self.translate_code_tab_widget, tr("translate_code_tab"))

    def _create_chat_history_area(self):
        # Creates the chat history display area.
        self.chat_history_widget = QWidget()
        chat_layout = QVBoxLayout(self.chat_history_widget)
        
        self.chat_history_display_label = QLabel(tr("chat_history_label"))
        chat_layout.addWidget(self.chat_history_display_label)
        
        self.chat_history_display = QTextEdit(self)
        self.chat_history_display.setReadOnly(True)
        chat_layout.addWidget(self.chat_history_display)

    def _load_api_key_and_model(self):
        # Loads API key and selected model from settings.
        self.api_key = self.settings.value("api_key", "")
        self.current_model_name = self.settings.value("gemini_model", DEFAULT_MODEL)
        if not self.api_key:
            self.statusBar().showMessage(tr("status_api_key_missing"))
        elif not self.current_model_name:
            self.statusBar().showMessage(tr("status_model_not_selected"))
        else:
            self.statusBar().showMessage(tr("status_ready"))

    def _open_settings(self):
        # Opens the settings dialog.
        dialog = SettingsDialog(self)
        dialog.settings_changed_signal.connect(self._on_settings_changed)
        dialog.exec_()

    def _on_settings_changed(self):
        # Handles actions after settings are changed and saved.
        self._load_api_key_and_model()
        old_lang = translation_current_language
        self._load_initial_language_and_translations()
        if old_lang != translation_current_language:
            self._retranslate_ui()
            QMessageBox.information(self, tr("settings_title"), tr("settings_saved_relaunch_lang"))
        else:
            QMessageBox.information(self, tr("settings_title"), tr("settings_saved_model_applied"))

    def _show_about_dialog(self):
        # Displays the About dialog with application information.
        developed_by_str = tr("app_developed_by", developer_name=self.app_developer)
        about_text_formatted = tr(
            "about_text", 
            app_name=tr(APP_NAME_KEY), 
            version=self.app_version, 
            developed_by=developed_by_str 
        )
        QMessageBox.about(self, tr("about_title"), about_text_formatted)

    def _load_docs_on_first_run(self):
        # Loads documentation context on the first run.
        first_run_setting = "docs_loaded_once"
        if not self.settings.value(first_run_setting, False, type=bool):
            self._read_docs_folder()
            self.settings.setValue(first_run_setting, True)
        else:
            self._read_docs_folder(silent=True)

    def _read_docs_folder(self, silent=False):
        # Reads documentation files to provide context to Gemini.
        self.docs_content_cache = ""
        doc_files_content = []
        if os.path.exists(self.docs_dir) and os.path.isdir(self.docs_dir):
            for filename in os.listdir(self.docs_dir):
                if filename.endswith((".txt", ".md")):
                    try:
                        with open(os.path.join(self.docs_dir, filename), 'r', encoding='utf-8') as f:
                            doc_files_content.append(f.read())
                    except Exception as e:
                        print(f"Error reading doc file '{filename}': {e}")
            if doc_files_content:
                self.docs_content_cache = "\\n\\n---\\n\\n".join(doc_files_content)
                if not silent:
                    self.statusBar().showMessage(tr("docs_loaded_info", len(doc_files_content)), 5000)
                return
        if not silent:
            if not os.path.exists(self.docs_dir):
                QMessageBox.information(self, tr("docs_not_found_info"), tr("docs_created_info"))
                self.statusBar().showMessage(tr("docs_created_info"), 5000)
            elif not doc_files_content:
                QMessageBox.information(self, tr("docs_not_found_info"), tr("docs_not_found_info"))
                self.statusBar().showMessage(tr("docs_not_found_info"), 5000)

    def start_gemini_task(self, prompt_text, result_display_widget, tab_name_for_log=""):
        # Starts a new Gemini API task in a separate thread.
        if self.thread and self.thread.isRunning():
            QMessageBox.information(self, tr("status_loading"), tr("task_already_running"))
            return

        if not self.api_key:
            QMessageBox.warning(self, tr("error_title"), tr("status_api_key_missing"))
            result_display_widget.setHtml(f"<p style='color:red;'>{tr('status_api_key_missing')}</p>")
            self.statusBar().showMessage(tr("status_api_key_missing"))
            return
        if not self.current_model_name:
            QMessageBox.warning(self, tr("error_title"), tr("status_model_not_selected"))
            result_display_widget.setHtml(f"<p style='color:red;'>{tr('status_model_not_selected')}</p>")
            self.statusBar().showMessage(tr("status_model_not_selected"))
            return

        self.statusBar().showMessage(tr("status_loading"))
        result_display_widget.setHtml(f"<p><i>{tr('status_loading')}</i></p>")

        self.thread = QThread(self)
        self.worker = GeminiWorker(
            self.api_key, self.current_model_name, prompt_text, self.docs_content_cache
        )
        self.worker.moveToThread(self.thread)

        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater) 
        self.thread.finished.connect(self.thread.deleteLater)

        self.worker.finished.connect(
            lambda result: self._on_gemini_finished(
                result, result_display_widget, prompt_text, tab_name_for_log
            )
        )
        self.worker.error.connect(
            lambda error_msg: self._on_gemini_error(error_msg, result_display_widget)
        )
        
        self.thread.started.connect(self.worker.run)
        self.thread.start()

    def _on_gemini_finished(self, result_markdown, result_display_widget, original_query, tab_name_for_log=""):
        # Handles successful Gemini API response.
        html_output = markdown2.markdown(result_markdown, extras=["fenced-code-blocks", "codehilite"])
        html_output_styled = (
            "<style>"
            "pre { background-color: #2b2b2b; color: #f0f0f0; padding: 10px; "
            "border-radius: 5px; overflow-x: auto; font-family: Consolas, monospace; } "
            "code { font-family: Consolas, monospace; }"
            "</style>"
            f"{html_output}"
        )
        result_display_widget.setHtml(html_output_styled)
        self.statusBar().showMessage(tr("status_ready"), 3000)
        self._log_interaction(
            f"({tab_name_for_log}) {original_query}" if tab_name_for_log else original_query,
            result_markdown
        )
        self._cleanup_thread_references()

    def _on_gemini_error(self, error_msg, result_display_widget):
        # Handles errors from Gemini API task.
        safe_error_msg = error_msg.replace('<', '<').replace('>', '>')
        error_html = f"<p style='color:red;'><b>{tr('error_title')}:</b> {safe_error_msg}</p>"
        result_display_widget.setHtml(error_html)
        self.statusBar().showMessage(tr("status_error"), 5000)
        self._log_interaction("API Error", error_msg)
        self._cleanup_thread_references()

    def _cleanup_thread_references(self):
        # Clears references to finished thread and worker.
        self.thread = None
        self.worker = None

    def _log_interaction(self, query, response_markdown):
        # Logs user query and Gemini response to a file and the UI chat history.
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = (
            f"--- {timestamp} ---\\n"
            f"User ({translation_current_language}):\\n{query}\\n\\n"
            f"Gemini ({self.current_model_name}):\\n{response_markdown}\\n\\n"
        )
        try:
            with open(self.chat_history_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Error writing to log file: {e}")
            self.statusBar().showMessage(tr("log_error"), 3000)
        
        query_html = query.replace('<', '<').replace('>', '>').replace('\\n', '<br>')
        response_html_for_chat = markdown2.markdown(response_markdown, extras=["fenced-code-blocks"])
        
        html_entry = (
            f'<p style="color: #aaa;"><b>--- {timestamp} ---</b></p>'
            f"<p><b>{tr('user_label_chat')}:</b></p>"
            f'<div style="background-color: #2A2A2A; padding: 8px; border-radius: 4px; margin-bottom: 5px; word-wrap: break-word;">{query_html}</div>'
            f"<p><b>Gemini ({self.current_model_name}):</b></p>"
            f'<div style="background-color: #2A2A2A; padding: 8px; border-radius: 4px; margin-bottom: 10px; word-wrap: break-word;">{response_html_for_chat}</div>'
            f'<hr style="border-color: #444;">'
        )
        self.chat_history_display.moveCursor(QTextCursor.End)
        self.chat_history_display.insertHtml(html_entry)
        self.chat_history_display.moveCursor(QTextCursor.End)

    def closeEvent(self, event):
        # Handles the main window close event, ensuring threads are stopped.
        reply = QMessageBox.question(
            self,
            tr("confirm_exit_title"),
            tr("confirm_exit_text"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if self.worker:
                self.worker.stop()
            if self.thread and self.thread.isRunning():
                self.thread.quit()
                if not self.thread.wait(2000):
                    print("Warning: Gemini Worker thread did not terminate gracefully.")
            event.accept()
        else:
            event.ignore()