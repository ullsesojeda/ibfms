import os

class Config:
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "IBFMS_Secret_2026"
    )

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///ibfms.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False