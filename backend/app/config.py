"""Настройки сервиса. Всё приходит из окружения (docker-compose)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://app:app@db:5432/registry"
    redis_url: str = "redis://redis:6379/0"

    llm_base_url: str = "http://llm-mock:8090/v1"
    llm_api_key: str = "mock-key"
    llm_model: str = "fast-model-free"
    llm_model_fallback: str = "fast-model-paid"

    # Верхняя граница на один HTTP-вызов к провайдеру. Обычная генерация
    # укладывается в 10 секунд, но на холодной модели бывает заметно дольше.
    llm_timeout_seconds: float = 45.0

    # Сколько попыток генерации делаем, если критик забраковал черновик,
    # и с какой оценки текст считается готовым к показу.
    ai_max_attempts: int = 2
    ai_min_score: int = 85

    # Сутки: описание завязано на отпечаток фактов и само протухает,
    # когда в карточке что-то меняется.
    ai_cache_ttl_seconds: int = 24 * 60 * 60

    # Сколько дизлайков подряд считаем сигналом «текст плохой».
    ai_dislikes_before_regeneration: int = 3
    ai_feedback_ttl_seconds: int = 7 * 24 * 60 * 60

    # echo=True у SQLAlchemy: удобно смотреть, что именно уходит в базу.
    log_sql: bool = False


settings = Settings()
