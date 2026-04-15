import json
import sys
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from PySide6.QtCore import QThread, QTimer, QUrl, Signal
from PySide6.QtGui import QAction, QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QProgressBar,
    QSplitter,
    QStatusBar,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from Modulos.AI_Provider import detectar_provedor, chamar_ia
from Modulos.app_config import AppConfig, carregar_config, config_valida, salvar_config
from Modulos.processor import corrigir_texto, gerar_resumo
from Modulos.transcript import obter_transcricao

WINDOW_TITLE = "YouTube Video Summarizer"
APP_VERSION = "v1.0.1"
LATEST_RELEASE_API_URL = "https://api.github.com/repos/enishi2/Video-Summarizer/releases/latest"
RELEASES_PAGE_URL = "https://github.com/enishi2/Video-Summarizer/releases"
LANGUAGE_OPTIONS = {
    "English": "English",
    "Portuguese": "Portuguese",
    "Spanish": "Spanish",
    "French": "French",
    "German": "German",
    "Italian": "Italian",
    "Japanese": "Japanese",
    "Chinese": "Chinese",
}

SYSTEM_PROMPT = """You are an assistant that answers questions about a specific video.

RULES:
1. Answer ONLY based on the video content below.
2. If the information is not in the video, say: "That was not mentioned in the video."
3. Never invent information.
4. Be clear and concise.

VIDEO CONTENT:
{conteudo}"""


@dataclass
class ProcessResult:
    summary: str
    transcript: str
    provider: str
    transcript_method: str
    url: str
    summary_language: str


@dataclass
class UpdateInfo:
    tag_name: str
    html_url: str
    body: str


class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API Settings")
        self.setModal(True)
        self.resize(520, 260)

        layout = QVBoxLayout(self)

        intro = QLabel(
            "Add at least one AI provider key. Groq is the recommended free option. "
            "Your keys are stored only on this computer."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        form = QFormLayout()

        self.groq_input = QLineEdit(config.groq_api_key)
        self.groq_input.setEchoMode(QLineEdit.Password)
        self.groq_input.setPlaceholderText("gsk_...")
        form.addRow("Groq API Key", self.groq_input)

        self.openai_input = QLineEdit(config.openai_api_key)
        self.openai_input.setEchoMode(QLineEdit.Password)
        self.openai_input.setPlaceholderText("sk-...")
        form.addRow("OpenAI API Key", self.openai_input)

        self.anthropic_input = QLineEdit(config.anthropic_api_key)
        self.anthropic_input.setEchoMode(QLineEdit.Password)
        self.anthropic_input.setPlaceholderText("sk-ant-...")
        form.addRow("Anthropic API Key", self.anthropic_input)

        self.languages_input = QLineEdit(config.transcript_languages)
        self.languages_input.setPlaceholderText("pt,en")
        form.addRow("Transcript languages", self.languages_input)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_config(self) -> AppConfig:
        return AppConfig(
            groq_api_key=self.groq_input.text().strip(),
            openai_api_key=self.openai_input.text().strip(),
            anthropic_api_key=self.anthropic_input.text().strip(),
            transcript_languages=self.languages_input.text().strip() or "pt,en",
        )


class SummarizeWorker(QThread):
    progress = Signal(str)
    finished_with_result = Signal(object)
    failed = Signal(str)

    def __init__(self, url: str, summary_language: str, parent=None):
        super().__init__(parent)
        self.url = url
        self.summary_language = summary_language

    def run(self):
        try:
            self.progress.emit("Detecting AI provider...")
            provider = detectar_provedor()

            self.progress.emit("Fetching transcript...")
            raw_transcript, transcript_method = obter_transcricao(self.url, provider)
            method_label = "YouTube captions" if transcript_method == "legenda" else "audio transcription"
            self.progress.emit(f"Transcript obtained via {method_label}.")

            self.progress.emit("Correcting transcript...")
            fixed_transcript = corrigir_texto(raw_transcript, provider)

            self.progress.emit("Generating summary...")
            summary = gerar_resumo(fixed_transcript, provider, idioma=self.summary_language)

            self.finished_with_result.emit(
                ProcessResult(
                    summary=summary,
                    transcript=fixed_transcript,
                    provider=provider,
                    transcript_method=transcript_method,
                    url=self.url,
                    summary_language=self.summary_language,
                )
            )
        except Exception as exc:
            self.failed.emit(str(exc))


class ChatWorker(QThread):
    finished_with_answer = Signal(str)
    failed = Signal(str)

    def __init__(self, provider: str, messages: list[dict], parent=None):
        super().__init__(parent)
        self.provider = provider
        self.messages = messages

    def run(self):
        try:
            answer = chamar_ia(self.provider, self.messages, max_tokens=800)
            self.finished_with_answer.emit(answer)
        except Exception as exc:
            self.failed.emit(str(exc))


class UpdateCheckWorker(QThread):
    update_available = Signal(object)
    status_message = Signal(str)

    def run(self):
        try:
            request = Request(
                LATEST_RELEASE_API_URL,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": f"video-summarizer/{APP_VERSION}",
                },
            )
            with urlopen(request, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))

            latest_tag = str(payload.get("tag_name", "")).strip()
            if not latest_tag or not _is_newer_version(latest_tag, APP_VERSION):
                return

            release_url = str(payload.get("html_url") or RELEASES_PAGE_URL)
            release_body = str(payload.get("body") or "").strip()
            self.update_available.emit(UpdateInfo(latest_tag, release_url, release_body))
        except (HTTPError, URLError, TimeoutError, ValueError, OSError):
            return
        except Exception as exc:
            self.status_message.emit(f"Update check skipped: {exc}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(1280, 860)

        self.config = carregar_config()
        self.worker = None
        self.chat_worker = None
        self.update_worker = None
        self.history = []
        self.current_provider = None
        self.current_summary = ""
        self.current_transcript = ""
        self.current_url = ""
        self.update_prompt_shown = False

        self._build_ui()
        self._build_menu()
        self._load_initial_state()
        QTimer.singleShot(1200, self.check_for_updates_silently)

    def _build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        header = QLabel("Summarize YouTube Videos")
        header.setStyleSheet("font-size: 24px; font-weight: 600;")
        root.addWidget(header)

        subheader = QLabel(
            "Use local execution for transcripts, keep your API keys on-device, and chat with the video after processing."
        )
        subheader.setWordWrap(True)
        subheader.setStyleSheet("color: #5b6472; font-size: 13px;")
        root.addWidget(subheader)

        controls_group = QGroupBox("Video")
        controls_layout = QVBoxLayout(controls_group)

        url_row = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.url_input.returnPressed.connect(self.start_processing)
        self.summarize_button = QPushButton("Summarize")
        self.summarize_button.clicked.connect(self.start_processing)
        url_row.addWidget(self.url_input, 1)
        url_row.addWidget(self.summarize_button)
        controls_layout.addLayout(url_row)

        options_row = QHBoxLayout()
        options_row.addWidget(QLabel("Summary language"))
        self.language_combo = QComboBox()
        self.language_combo.addItems(LANGUAGE_OPTIONS.keys())
        options_row.addWidget(self.language_combo)
        options_row.addStretch(1)
        self.provider_label = QLabel(f"Provider: not checked | Version: {APP_VERSION}")
        self.provider_label.setStyleSheet("color: #5b6472;")
        options_row.addWidget(self.provider_label)
        controls_layout.addLayout(options_row)

        root.addWidget(controls_group)

        self.progress_label = QLabel("Ready")
        self.progress_label.setStyleSheet("font-size: 13px; color: #384152;")
        root.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        root.addWidget(self.progress_bar)

        splitter = QSplitter()

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        summary_title = QLabel("Summary")
        summary_title.setStyleSheet("font-size: 18px; font-weight: 600;")
        left_layout.addWidget(summary_title)

        self.summary_view = QTextBrowser()
        left_layout.addWidget(self.summary_view, 3)

        transcript_title = QLabel("Transcript")
        transcript_title.setStyleSheet("font-size: 18px; font-weight: 600;")
        left_layout.addWidget(transcript_title)

        self.transcript_view = QPlainTextEdit()
        self.transcript_view.setReadOnly(True)
        self.transcript_view.setPlaceholderText("The corrected transcript will appear here.")
        left_layout.addWidget(self.transcript_view, 2)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        chat_title = QLabel("Ask About The Video")
        chat_title.setStyleSheet("font-size: 18px; font-weight: 600;")
        right_layout.addWidget(chat_title)

        self.chat_view = QTextBrowser()
        right_layout.addWidget(self.chat_view, 1)

        self.chat_input = QTextEdit()
        self.chat_input.setPlaceholderText("Ask anything about the current video...")
        self.chat_input.setFixedHeight(100)
        right_layout.addWidget(self.chat_input)

        self.ask_button = QPushButton("Ask")
        self.ask_button.clicked.connect(self.ask_question)
        self.ask_button.setEnabled(False)
        right_layout.addWidget(self.ask_button)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([780, 420])
        root.addWidget(splitter, 1)

        self.setCentralWidget(central)

        status_bar = QStatusBar()
        status_bar.showMessage("Desktop app ready")
        self.setStatusBar(status_bar)

    def _build_menu(self):
        menu = self.menuBar().addMenu("File")

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        menu.addAction(settings_action)

        check_updates_action = QAction("Check for Updates", self)
        check_updates_action.triggered.connect(self.check_for_updates_manually)
        menu.addAction(check_updates_action)

        clear_action = QAction("Clear Results", self)
        clear_action.triggered.connect(self.clear_results)
        menu.addAction(clear_action)

        menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        menu.addAction(quit_action)

    def _load_initial_state(self):
        if not config_valida(self.config):
            QMessageBox.information(
                self,
                WINDOW_TITLE,
                "Configure at least one AI provider key before starting.",
            )
            self.open_settings(force=True)
        else:
            self._apply_config(self.config)

    def _apply_config(self, config: AppConfig):
        self.config = config
        self.config.apply_to_environment()

    def open_settings(self, force: bool = False):
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() != QDialog.Accepted:
            if force and not config_valida(self.config):
                self.close()
            return

        new_config = dialog.get_config()
        if not config_valida(new_config):
            QMessageBox.warning(self, WINDOW_TITLE, "Add at least one API key to continue.")
            if force:
                self.open_settings(force=True)
            return

        salvar_config(new_config)
        self._apply_config(new_config)
        self.statusBar().showMessage("Settings saved", 4000)

    def clear_results(self):
        self.history.clear()
        self.current_provider = None
        self.current_summary = ""
        self.current_transcript = ""
        self.current_url = ""
        self.summary_view.clear()
        self.transcript_view.clear()
        self.chat_view.clear()
        self.chat_input.clear()
        self.ask_button.setEnabled(False)
        self.provider_label.setText(f"Provider: not checked | Version: {APP_VERSION}")
        self.progress_label.setText("Ready")
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.statusBar().showMessage("Results cleared", 4000)

    def start_processing(self):
        if self.worker and self.worker.isRunning():
            QMessageBox.information(self, WINDOW_TITLE, "A summary is already being generated.")
            return

        if not config_valida(self.config):
            self.open_settings(force=True)
            return

        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, WINDOW_TITLE, "Paste a YouTube URL before starting.")
            return

        summary_language = LANGUAGE_OPTIONS[self.language_combo.currentText()]
        self.history.clear()
        self.chat_view.clear()
        self.summary_view.clear()
        self.transcript_view.clear()
        self.ask_button.setEnabled(False)
        self.current_summary = ""
        self.current_transcript = ""
        self.current_provider = None
        self.current_url = url

        self.progress_bar.setRange(0, 0)
        self.progress_label.setText("Preparing...")
        self.statusBar().showMessage("Processing video...")
        self.summarize_button.setEnabled(False)

        self.worker = SummarizeWorker(url, summary_language, self)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished_with_result.connect(self.on_processing_finished)
        self.worker.failed.connect(self.on_processing_failed)
        self.worker.finished.connect(self._cleanup_worker_reference)
        self.worker.start()

    def _cleanup_worker_reference(self):
        self.worker = None

    def on_progress(self, message: str):
        self.progress_label.setText(message)
        self.statusBar().showMessage(message)

    def on_processing_finished(self, result: ProcessResult):
        self.summarize_button.setEnabled(True)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)
        self.progress_label.setText("Summary ready")
        self.statusBar().showMessage("Video processed successfully", 4000)

        self.current_provider = result.provider
        self.current_summary = result.summary
        self.current_transcript = result.transcript
        self.current_url = result.url

        self.provider_label.setText(f"Provider: {result.provider.upper()} | Version: {APP_VERSION}")
        self.summary_view.setMarkdown(result.summary)
        self.transcript_view.setPlainText(result.transcript)
        self.ask_button.setEnabled(True)

    def on_processing_failed(self, message: str):
        self.summarize_button.setEnabled(True)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Processing failed")
        self.statusBar().showMessage("An error interrupted processing", 5000)
        QMessageBox.critical(self, WINDOW_TITLE, message)

    def ask_question(self):
        if self.chat_worker and self.chat_worker.isRunning():
            QMessageBox.information(self, WINDOW_TITLE, "Wait for the current answer to finish.")
            return

        question = self.chat_input.toPlainText().strip()
        if not question:
            return

        if not self.current_summary or not self.current_transcript or not self.current_provider:
            QMessageBox.warning(self, WINDOW_TITLE, "Generate a summary before using the chat.")
            return

        self._append_chat("You", question)
        self.chat_input.clear()
        self.history.append({"role": "user", "content": question})

        content = (
            f"=== SUMMARY ===\n{self.current_summary}\n\n"
            f"=== FULL TRANSCRIPT ===\n{self.current_transcript}"
        )
        system = SYSTEM_PROMPT.format(conteudo=content[:15000])
        messages = [{"role": "system", "content": system}] + self.history

        self.ask_button.setEnabled(False)
        self.statusBar().showMessage("Generating answer...")
        self.chat_worker = ChatWorker(self.current_provider, messages, self)
        self.chat_worker.finished_with_answer.connect(self.on_chat_finished)
        self.chat_worker.failed.connect(self.on_chat_failed)
        self.chat_worker.finished.connect(self._cleanup_chat_worker_reference)
        self.chat_worker.start()

    def _cleanup_chat_worker_reference(self):
        self.chat_worker = None

    def on_chat_finished(self, answer: str):
        self.ask_button.setEnabled(True)
        self._append_chat("Assistant", answer)
        self.history.append({"role": "assistant", "content": answer})
        if len(self.history) > 20:
            self.history = self.history[-20:]
        self.statusBar().showMessage("Answer ready", 4000)

    def on_chat_failed(self, message: str):
        self.ask_button.setEnabled(True)
        if self.history and self.history[-1]["role"] == "user":
            self.history.pop()
        self.statusBar().showMessage("Chat failed", 5000)
        QMessageBox.critical(self, WINDOW_TITLE, message)

    def _append_chat(self, speaker: str, text: str):
        safe_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        self.chat_view.append(f"<p><b>{speaker}:</b><br>{safe_text}</p>")

    def check_for_updates_silently(self):
        self._start_update_check(manual=False)

    def check_for_updates_manually(self):
        self._start_update_check(manual=True)

    def _start_update_check(self, manual: bool):
        if self.update_worker and self.update_worker.isRunning():
            if manual:
                QMessageBox.information(self, WINDOW_TITLE, "An update check is already in progress.")
            return

        self.update_prompt_shown = False
        self.update_worker = UpdateCheckWorker(self)
        self.update_worker.update_available.connect(self.on_update_available)
        self.update_worker.status_message.connect(self.on_update_status_message)
        self.update_worker.finished.connect(self._cleanup_update_worker_reference)
        self.update_worker.finished.connect(lambda: self._notify_no_updates_if_manual(manual))
        self.update_worker.start()

    def _cleanup_update_worker_reference(self):
        self.update_worker = None

    def _notify_no_updates_if_manual(self, manual: bool):
        if manual and not self.update_prompt_shown:
            QMessageBox.information(
                self,
                WINDOW_TITLE,
                f"You are already using the latest version available on GitHub Releases ({APP_VERSION}).",
            )
        self.update_prompt_shown = False

    def on_update_available(self, update_info: UpdateInfo):
        self.update_prompt_shown = True
        message = QMessageBox(self)
        message.setWindowTitle("Update Available")
        message.setIcon(QMessageBox.Information)
        notes = update_info.body[:600].strip()
        details = f"\n\nRelease notes preview:\n{notes}" if notes else ""
        message.setText(
            f"A newer version is available: {update_info.tag_name}.\n"
            f"Current version: {APP_VERSION}.{details}\n\n"
            "Do you want to open the GitHub release page?"
        )
        message.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        if message.exec() == QMessageBox.Yes:
            QDesktopServices.openUrl(QUrl(update_info.html_url))

    def on_update_status_message(self, message: str):
        self.statusBar().showMessage(message, 4000)


def _parse_version_tuple(version: str) -> tuple[int, ...]:
    cleaned = version.strip().lower().lstrip("v")
    parts = []
    for raw_part in cleaned.split("."):
        digits = "".join(ch for ch in raw_part if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def _is_newer_version(candidate: str, current: str) -> bool:
    candidate_tuple = _parse_version_tuple(candidate)
    current_tuple = _parse_version_tuple(current)
    max_len = max(len(candidate_tuple), len(current_tuple))
    candidate_tuple += (0,) * (max_len - len(candidate_tuple))
    current_tuple += (0,) * (max_len - len(current_tuple))
    return candidate_tuple > current_tuple


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(WINDOW_TITLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
