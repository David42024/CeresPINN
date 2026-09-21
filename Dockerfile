# CeresPINN backend — FastAPI + PINN (Python 3.12)
# Build context is the repository root so `backend` is importable as a package.

FROM python:3.12-slim AS runtime

# System libs required by some wheels (psycopg2-binary, netCDF4) and curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only the requirements first to leverage Docker layer caching
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements.txt

# Copy the rest of the backend and the start script
COPY backend ./backend
COPY backend/start.sh ./backend/start.sh

# Validate the exact production checkpoint while building. A bad/missing model
# must fail the deploy instead of activating the calibrated surrogate.
RUN python -c "from backend.inference import get_inference; i=get_inference(); assert i.load_model() is not None, i.error_message"

# Render injects PORT at runtime; this is just the default.
ENV PORT=8000
ENV CERESPINN_MODEL_DIR=/app/backend/models
ENV CERESPINN_REQUIRE_MODEL=1

EXPOSE 8000
CMD ["bash", "backend/start.sh"]
