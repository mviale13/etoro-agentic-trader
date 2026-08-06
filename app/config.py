from functools import lru_cache
from typing import Annotated, Any, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    trading_mode: Literal["paper", "demo", "approval", "real"] = "paper"
    live_trading_enabled: bool = False
    live_confirmation: str = ""
    etoro_api_key: str = ""
    etoro_user_key: str = ""
    etoro_base_url: str = "https://public-api.etoro.com"
    database_url: str = "sqlite:///./trader.db"

    # The Communication layer's writing providers, read from .env like
    # the broker keys. A process environment variable of the same name
    # wins, which is pydantic-settings' own precedence.
    anthropic_api_key: str = ""
    anthropic_auth_token: str = ""
    openai_api_key: str = ""
    movrvest_executive_writer: str = ""
    movrvest_writer_provider: str = ""
    movrvest_writer_model: str = ""

    # The model that reads a filing, configured apart from the one that
    # words a case. Reading is evidence and wording is formatting, so a
    # decision taken about one must not quietly change the other.
    movrvest_reader_provider: str = ""
    movrvest_reader_model: str = ""

    allowed_symbols: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["BTC", "ETH", "SOL", "SPY", "QQQ"]
    )
    crypto_symbols: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["BTC", "ETH", "SOL"]
    )

    allow_crypto: bool = True
    allow_shorts: bool = False
    max_leverage: int = 1
    max_portfolio_capital_usd: float = 2000
    max_position_pct: float = 0.05
    max_crypto_exposure_pct: float = 0.20
    max_daily_loss_pct: float = 0.015
    max_open_positions: int = 5
    max_order_usd: float = 100
    min_stop_loss_pct: float = 0.01
    max_stop_loss_pct: float = 0.05
    min_take_profit_pct: float = 0.02
    max_trades_per_day: int = 5
    require_manual_approval: bool = True

    @field_validator("allowed_symbols", "crypto_symbols", mode="before")
    @classmethod
    def split_csv(cls, value: Any) -> Any:
        if isinstance(value, str):
            return [item.strip().upper() for item in value.split(",") if item.strip()]
        return value

    @property
    def live_gate_open(self) -> bool:
        return (
            self.trading_mode == "real"
            and self.live_trading_enabled
            and self.live_confirmation == "I_ACCEPT_REAL_MONEY_RISK"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
