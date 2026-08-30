import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "IBFMS_Secret_2026"
    )

    if os.name == "nt":
        # Windows (desarrollo)
        SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(
            BASE_DIR,
            "instance",
            "ibfms.db"
        )
    else:
        # Render (Linux)
        SQLALCHEMY_DATABASE_URI = os.getenv(
            "DATABASE_URL",
            "sqlite:////montesion/vigilancia/ibfms.db"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False