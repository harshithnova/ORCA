from providers.imd.adapter import IMD_KOCHI_URL
from providers.imd.normalize import normalize_kochi_weather


result = normalize_kochi_weather(
    "data/raw/imd_kochi.html",
    "data/normalized/kochi_imd.json",
    IMD_KOCHI_URL,
)

print(result)