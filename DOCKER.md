# Docker Setup Guide

This guide explains how to run the AI Translation Pipeline using Docker containers.

## Prerequisites

1. **Docker** and **Docker Compose** installed
   - Docker Desktop: https://www.docker.com/products/docker-desktop
   - Or Docker Engine + Docker Compose: https://docs.docker.com/compose/install/

2. **Ollama** running on your host machine
   - Download: https://ollama.ai
   - Start Ollama: `ollama serve`
   - Pull the model: `ollama pull mistral:7b`

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Chaima-Ja/AIMultiModalTranslating.git
   cd AIMultiModalTranslating
   ```

2. **Build and start the containers:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - Web UI: http://localhost:8501
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Architecture

The Docker setup includes:

- **API Service** (`api`): FastAPI backend running on port 8000
- **UI Service** (`ui`): Streamlit web interface running on port 8501
- **Ollama**: Must run separately on the host (or in a separate container)

## Configuration

### Environment Variables

You can configure the services using environment variables in `docker-compose.yml`:

```yaml
environment:
  - OLLAMA_URL=http://host.docker.internal:11434  # Ollama endpoint
  - OLLAMA_MODEL=mistral:7b                        # Model to use
  - WHISPER_MODEL=medium                            # Whisper model size
  - WHISPER_DEVICE=cpu                              # cpu or cuda
  - TTS_MODEL=tts_models/multilingual/multi-dataset/xtts_v2
  - TTS_DEVICE=cpu                                  # cpu or cuda
  - TTS_LANGUAGE=fr                                 # Target language
  - TRANSLATION_CONCURRENCY=5                      # Parallel translations
```

### Running Ollama in Docker (Optional)

If you want to run Ollama in Docker as well, uncomment the Ollama service in `docker-compose.yml`:

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped

volumes:
  ollama_data:
```

Then update the `OLLAMA_URL` in the API service to `http://ollama:11434`.

## Usage

### Start Services

```bash
# Start in foreground (see logs)
docker-compose up

# Start in background
docker-compose up -d

# Rebuild and start
docker-compose up --build
```

### Stop Services

```bash
# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop, remove containers, and volumes
docker-compose down -v
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f ui
```

### Rebuild After Code Changes

```bash
# Rebuild and restart
docker-compose up --build

# Or rebuild without cache
docker-compose build --no-cache
docker-compose up
```

## File Persistence

The `uploads/` and `outputs/` directories are mounted as volumes, so:
- Uploaded files persist between container restarts
- Translated files are accessible on the host
- Files are stored in `./uploads` and `./outputs` on your host machine

## Troubleshooting

### API Can't Connect to Ollama

If the API can't reach Ollama:

1. **Check Ollama is running:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. **On Linux**, `host.docker.internal` might not work. Use:
   ```yaml
   environment:
     - OLLAMA_URL=http://172.17.0.1:11434  # Docker bridge IP
   ```
   Or add to `docker-compose.yml`:
   ```yaml
   extra_hosts:
     - "host.docker.internal:host-gateway"
   ```

3. **On macOS/Windows**, `host.docker.internal` should work by default.

### TTS Not Working

If TTS features aren't working:

1. **Check TTS installation:**
   ```bash
   docker-compose exec api python -c "from TTS.api import TTS; print('TTS OK')"
   ```

2. **Check logs for errors:**
   ```bash
   docker-compose logs api | grep -i tts
   ```

3. **Verify dependencies:**
   ```bash
   docker-compose exec api pip list | grep -E "TTS|soundfile|scipy|llvmlite|numba"
   ```

### GPU Support (CUDA)

To use GPU for Whisper/TTS:

1. **Install nvidia-docker2:**
   ```bash
   # Follow: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
   ```

2. **Update docker-compose.yml:**
   ```yaml
   services:
     api:
       deploy:
         resources:
           reservations:
             devices:
               - driver: nvidia
                 count: 1
                 capabilities: [gpu]
       environment:
         - WHISPER_DEVICE=cuda
         - TTS_DEVICE=cuda
   ```

3. **Rebuild:**
   ```bash
   docker-compose up --build
   ```

### Port Conflicts

If ports 8000 or 8501 are already in use:

1. **Change ports in docker-compose.yml:**
   ```yaml
   services:
     api:
       ports:
         - "8001:8000"  # Host:Container
     ui:
       ports:
         - "8502:8501"
   ```

2. **Update UI API URL:**
   ```yaml
   services:
     ui:
       environment:
         - API_BASE_URL=http://api:8000  # Internal Docker network
   ```

## Development

### Building the Image Manually

```bash
docker build -t ai-translator:latest .
```

### Running a Container Manually

```bash
# API only
docker run -p 8000:8000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/outputs:/app/outputs \
  -e OLLAMA_URL=http://host.docker.internal:11434 \
  ai-translator:latest python start_api.py

# UI only
docker run -p 8501:8501 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/outputs:/app/outputs \
  -e API_BASE_URL=http://host.docker.internal:8000 \
  ai-translator:latest streamlit run ui.py --server.address=0.0.0.0 --server.port=8501
```

### Accessing Container Shell

```bash
# API container
docker-compose exec api bash

# UI container
docker-compose exec ui bash
```

## Production Considerations

For production deployment:

1. **Use environment files:**
   ```bash
   # .env file
   OLLAMA_URL=http://ollama-service:11434
   OLLAMA_MODEL=mistral:7b
   WHISPER_DEVICE=cuda
   TTS_DEVICE=cuda
   ```

2. **Add health checks** (already included)

3. **Set resource limits:**
   ```yaml
   services:
     api:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 4G
   ```

4. **Use a reverse proxy** (nginx/traefik) for HTTPS

5. **Set up logging** to external service

6. **Use secrets management** for sensitive config

## Support

For issues or questions:
- Check logs: `docker-compose logs`
- Verify Ollama: `curl http://localhost:11434/api/tags`
- Check container status: `docker-compose ps`
- Review Dockerfile for dependency versions

