"""Configuration loader for The Silent Cartographer."""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file="config.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Paths
    tsc_kindle_dir: Path = Field(
        default=Path(r"C:\Users\carlo\Documents\Kindle Exports"),
        description="Directory containing Kindle HTML exports",
    )
    tsc_vault_path: Path = Field(
        default=Path(r"C:\Users\carlo\Documents\The Library"),
        description="Path to Obsidian vault",
    )
    tsc_template_path: Path = Field(
        default=Path(r"C:\Users\carlo\Documents\The Silent Cartographer\template.md"),
        description="Path to concept note template",
    )
    tsc_profile_path: Path = Field(
        default=Path(r"C:\Users\carlo\Documents\The Silent Cartographer\profile.md"),
        description="Path to user profile for context",
    )

    # LLM Configuration
    llm_mode: str = Field(
        default="cli",
        description="LLM mode: 'cli' (use claude command) or 'api' (use Anthropic API)",
    )

    # Anthropic API
    anthropic_api_key: str = Field(
        default="",
        description="Anthropic API key for Claude",
    )

    # Asana Integration
    asana_access_token: str = Field(
        default="",
        description="Asana personal access token",
    )
    asana_workspace_gid: str = Field(
        default="",
        description="Asana workspace GID",
    )
    asana_project_gid: str = Field(
        default="",
        description="Asana project GID for tasks",
    )

    # Email (SMTP)
    smtp_host: str = Field(
        default="smtp.gmail.com",
        description="SMTP server host",
    )
    smtp_port: int = Field(
        default=587,
        description="SMTP server port",
    )
    smtp_user: str = Field(
        default="",
        description="SMTP username/email",
    )
    smtp_password: str = Field(
        default="",
        description="SMTP password or app password",
    )
    tsc_email_to: str = Field(
        default="",
        description="Email recipient for notifications",
    )

    @property
    def books_dir(self) -> Path:
        """Path to Books folder in vault."""
        return self.tsc_vault_path / "Books"

    @property
    def ideas_dir(self) -> Path:
        """Path to Ideas folder in vault."""
        return self.tsc_vault_path / "Ideas"

    @property
    def processed_dir(self) -> Path:
        """Path to processed exports folder."""
        return self.tsc_kindle_dir / "processed"

    @property
    def memory_file(self) -> Path:
        """Path to memory tracking file."""
        return Path(__file__).parent.parent / ".memory.json"


# Global settings instance
_settings: Optional[Settings] = None


def get_settings(env_file: Optional[Path] = None) -> Settings:
    """Get or create settings instance.

    Args:
        env_file: Optional path to environment file. If not provided,
                  looks for config.env in the project root.

    Returns:
        Settings instance.
    """
    global _settings

    if _settings is None or env_file is not None:
        if env_file:
            _settings = Settings(_env_file=env_file)
        else:
            # Try to find config.env in project root
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config.env"
            if config_path.exists():
                _settings = Settings(_env_file=config_path)
            else:
                _settings = Settings()

    return _settings


def reset_settings() -> None:
    """Reset settings instance (useful for testing)."""
    global _settings
    _settings = None
