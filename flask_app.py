try:
    from dotenv import load_dotenv; load_dotenv()
except Exception:
    pass
from app import create_app
from app.config import ProductionConfig

app = create_app(ProductionConfig)
