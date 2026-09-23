FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8501

# Regenerate exports at container start, then serve the dashboard.
CMD ["sh", "-c", "python -m src.pipeline && streamlit run dashboard/app.py --server.headless true --server.port 8501"]
