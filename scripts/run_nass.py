import os
os.environ["CERESPINN_DRY_RUN"] = "0"
os.environ["NASS_API_KEY"] = "3681183C-FF1C-3A61-8CED-2293B7FC6359"
os.environ["NASS_STATE_ALPHA"] = "IA"

from backend.data.config import Settings
from backend.data.nass import NASSProvider

def main():
    settings = Settings()
    provider = NASSProvider(settings)
    print("Iniciando extracción NASS real...")
    res = provider.extract()
    print("Resultado:", res)

if __name__ == "__main__":
    main()
