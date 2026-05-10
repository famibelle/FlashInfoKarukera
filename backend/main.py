from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.services.horoscope_service import HoroscopeService
from datetime import date

app = FastAPI(
    title="FlashInfoKarukera API",
    description="API pour l'horoscope Karukera",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "FlashInfoKarukera Backend - API Horoscope"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/horoscope")
async def get_horoscope(date: date = None, edition: str = "matin"):
    """Récupère l'horoscope pour une date et une édition données"""
    if date is None:
        date = date.today()
    
    try:
        horoscope = await HoroscopeService.fetch_horoscope(
            date=date,
            edition=edition,
            n_signs=3
        )
        return horoscope.model_dump()
    except Exception as e:
        return {"error": str(e)}


@app.get("/signs")
async def get_all_signs():
    """Liste tous les signes du zodiaque"""
    return (await HoroscopeService.get_all_zodiac_signs()).model_dump()
