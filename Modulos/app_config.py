import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

CONFIG_DIR = Path.home() / '.youtube_summarizer'
CONFIG_FILE = CONFIG_DIR / 'config.json'
DEFAULT_TRANSCRIPT_LANGUAGES = 'pt,en'


@dataclass
class AppConfig:
    groq_api_key: str = ''
    openai_api_key: str = ''
    anthropic_api_key: str = ''
    transcript_languages: str = DEFAULT_TRANSCRIPT_LANGUAGES

    def apply_to_environment(self):
        os.environ['GROQ_API_KEY'] = self.groq_api_key
        os.environ['OPENAI_API_KEY'] = self.openai_api_key
        os.environ['ANTHROPIC_API_KEY'] = self.anthropic_api_key
        os.environ['TRANSCRIPT_LANGUAGES'] = self.transcript_languages or DEFAULT_TRANSCRIPT_LANGUAGES

    def to_dict(self) -> dict:
        return asdict(self)


def carregar_config() -> AppConfig:
    if not CONFIG_FILE.exists():
        return AppConfig()

    try:
        data = json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
    except Exception:
        return AppConfig()

    return AppConfig(
        groq_api_key=data.get('GROQ_API_KEY', data.get('groq_api_key', '')),
        openai_api_key=data.get('OPENAI_API_KEY', data.get('openai_api_key', '')),
        anthropic_api_key=data.get('ANTHROPIC_API_KEY', data.get('anthropic_api_key', '')),
        transcript_languages=data.get('TRANSCRIPT_LANGUAGES', data.get('transcript_languages', DEFAULT_TRANSCRIPT_LANGUAGES)),
    )


def salvar_config(config: AppConfig):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        'GROQ_API_KEY': config.groq_api_key,
        'OPENAI_API_KEY': config.openai_api_key,
        'ANTHROPIC_API_KEY': config.anthropic_api_key,
        'TRANSCRIPT_LANGUAGES': config.transcript_languages or DEFAULT_TRANSCRIPT_LANGUAGES,
    }
    CONFIG_FILE.write_text(json.dumps(payload, indent=2), encoding='utf-8')


def config_valida(config: AppConfig) -> bool:
    return bool(config.groq_api_key or config.openai_api_key or config.anthropic_api_key)
