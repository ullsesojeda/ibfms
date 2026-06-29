import os

class Config:
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "IBFMS_Secret_2026"
    )

    SQLALCHEMY_DATABASE_URI = (
        "sqlite:////montesion/vigilancia/ibfms.db"
        if os.getenv("RENDER")
        else "sqlite:///instance/ibfms.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
