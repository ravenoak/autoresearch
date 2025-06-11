# API Usage

The HTTP API is served via FastAPI. Start the server with Uvicorn:

```bash
uvicorn autoresearch.api:app --reload
```

Once running you can send a POST request:

```bash
curl -X POST http://localhost:8000/query -d '{"query": "explain machine learning"}' -H "Content-Type: application/json"
```
