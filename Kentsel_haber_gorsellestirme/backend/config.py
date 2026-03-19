# Ayarlar, env okuma
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "kocaeli_haberler")
GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
GEOCODING_KEY = os.getenv("GOOGLE_GEOCODING_API_KEY")