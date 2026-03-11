FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev
COPY . .
EXPOSE 8080
CMD ["uv", "run", "streamlit", "run", "3_data_dashboard/app.py", "--server.port", "8080", "--server.address", "0.0.0.0", "--server.headless", "true"]
