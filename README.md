# 🤖 Chatbot Using Pretrained Model

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-Transformers-FFD21E?logo=huggingface&logoColor=black)](https://huggingface.co/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

A production-ready AI chatbot web application built with FastAPI and Microsoft DialoGPT. It includes a polished dark-themed UI, robust input validation, rate limiting, timeout handling, environment-based configuration, and Docker support.

## Demo

Add a screenshot or GIF to `docs/demo.gif` (or any path you prefer), then reference it here:

```md
![Chatbot Demo](docs/demo.gif)
```

Suggested capture flow:
1. Start the app.
2. Send 2-3 user prompts.
3. Show clear chat behavior.
4. Show an error case (for example, forced timeout or rate limit).

## Features

- FastAPI backend with clean endpoint design and async inference timeout control.
- DialoGPT integration through Hugging Face Transformers and PyTorch.
- Stateful conversational memory with configurable max history.
- Input validation with length checks and basic XSS pattern blocking.
- Global and endpoint-specific rate limiting using `slowapi`.
- Graceful error handling for validation, timeout, and server failures.
- Modern glassmorphism dark UI with typing indicator and responsive design.
- Centralized `.env`-driven configuration via `python-dotenv`.
- Dockerfile + Docker Compose for reproducible deployment.
- Health endpoint for container health checks and monitoring systems.

## Project Structure

```text
chatbot-using-pretrained-model/
├── main.py
├── model.py
├── config.py
├── templates/
│   └── index.html
├── static/
│   ├── style.css
│   └── script.js
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Run Locally

### Option 1: Python

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows PowerShell

pip install -r requirements.txt
python main.py
```

App URL: [http://localhost:8000](http://localhost:8000)

### Option 2: Docker Compose

```bash
docker compose up --build
```

App URL: [http://localhost:8000](http://localhost:8000)

To stop:

```bash
docker compose down
```

## Configuration

All settings are controlled through environment variables.

| Variable | Default | Description |
|---|---|---|
| `MODEL_NAME` | `microsoft/DialoGPT-small` | Hugging Face model ID (`small`, `medium`, `large`) |
| `MAX_HISTORY_LENGTH` | `5` | Conversation turns to keep in context |
| `MAX_INPUT_LENGTH` | `500` | Max user message length in characters |
| `HOST` | `0.0.0.0` | FastAPI/uvicorn host |
| `PORT` | `8000` | Application port |
| `DEBUG` | `false` | Enables debug-level logging and reload behavior |
| `RATE_LIMIT` | `20/minute` | Default limiter for general endpoints |
| `RATE_LIMIT_CHAT` | `10/minute` | Stricter limiter for `/chat` endpoint |
| `MAX_NEW_TOKENS` | `200` | Max generated tokens per model response |
| `TEMPERATURE` | `0.7` | Sampling temperature |
| `TOP_P` | `0.9` | Nucleus sampling threshold |
| `TOP_K` | `50` | Top-k sampling cutoff |
| `REPETITION_PENALTY` | `1.2` | Penalizes repeated output patterns |
| `MODEL_TIMEOUT` | `30` | Inference timeout in seconds |

## Model Comparison

| Model | Approx Size | Typical RAM Need | Response Quality | Speed |
|---|---|---|---|---|
| `DialoGPT-small` | ~117M params | Low | Good for simple chat | Fast |
| `DialoGPT-medium` | ~345M params | Medium | Better coherence | Medium |
| `DialoGPT-large` | ~762M params | High | Best quality of the three | Slowest |

Recommendation:
- Start with `small` for local machines and quick iteration.
- Use `medium` when you want better output quality with moderate hardware.
- Use `large` only when quality is prioritized and memory is sufficient.

## Deployment

### Render
- Create a Web Service from your repository.
- Set build command: `pip install -r requirements.txt`
- Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Add environment variables from `.env.example`.

### Railway
- Create a new project from GitHub repo.
- Railway can auto-detect Python or Docker.
- Set env vars in Railway dashboard and deploy.

### Fly.io
- Use Docker deployment (`fly launch`).
- Ensure `PORT` is exposed and app binds to `0.0.0.0`.
- Set required secrets with `fly secrets set`.

### AWS EC2
- Install Docker + Docker Compose.
- Clone repo and run `docker compose up -d --build`.
- Open security group port (for example, 8000 or 80 with reverse proxy).

### Google Cloud Run
- Build and push Docker image.
- Deploy image to Cloud Run with public access as needed.
- Pass all environment variables in service configuration.

### Docker on Any VPS
- Install Docker Engine.
- Copy project and `.env` file.
- Run `docker compose up -d --build`.
- Put Nginx/Caddy in front for TLS and domain routing.

## API Reference

Base URL: `http://localhost:8000`

### `GET /`
Renders the chatbot web interface.

### `POST /chat`
Generate a response for a user message.

Request:

```json
{
  "message": "Hello, how are you?"
}
```

Success response (`200`):

```json
{
  "response": "I'm doing well! How can I help you today?",
  "status": "success"
}
```

Validation error (`400`):

```json
{
  "detail": "Message cannot be empty.",
  "status": "error"
}
```

Timeout error (`504`):

```json
{
  "detail": "Model response timed out. Please try again.",
  "status": "error"
}
```

Rate limit error (`429`, from slowapi):

```json
{
  "error": "Rate limit exceeded: 10 per 1 minute"
}
```

### `POST /clear`
Clears in-memory chat history.

Success response (`200`):

```json
{
  "status": "success",
  "message": "Chat history cleared."
}
```

### `GET /health`
Returns health and model metadata.

Example response (`200`):

```json
{
  "status": "healthy",
  "model_name": "microsoft/DialoGPT-small",
  "max_history": 5,
  "model_loaded": true
}
```

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI, Uvicorn |
| AI Model | Microsoft DialoGPT (Hugging Face Transformers) |
| Inference Runtime | PyTorch |
| Templating | Jinja2 |
| Frontend | HTML, CSS, Vanilla JavaScript |
| Config Management | python-dotenv |
| Rate Limiting | slowapi |
| Containerization | Docker, Docker Compose |

## License

This project is licensed under the MIT License.
