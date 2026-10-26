import os
os.environ["CERESPINN_DRY_RUN"] = "0"
os.environ["NASS_STATE_ALPHA"] = "IA"

from backend.data.config import Settings
from backend.data.nass import NASSProvider

def main():
    if not os.environ.get("NASS_API_KEY"):
        raise RuntimeError("Set NASS_API_KEY in the environment before downloading data")
    settings = Settings()
    provider = NASSProvider(settings)
    print("Iniciando extracción NASS real...")
    res = provider.extract()
    print("Resultado:", res)

if __name__ == "__main__":
    main()
