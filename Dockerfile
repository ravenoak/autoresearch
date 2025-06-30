FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir poetry \
    && poetry install --with dev --no-interaction
EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "autoresearch.api:app", "--host", "0.0.0.0", "--port", "8000"]
