from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./civisense.db"
    upload_dir: str = "./uploads"
    cors_origins: str = "http://localhost:5173,http://localhost:5174,http://localhost:5180"
    jwt_secret: str = "dev-secret-change-me-in-production"
    jwt_expire_minutes: int = 10080  # 7 days

    class Config:
        env_file = ".env"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
