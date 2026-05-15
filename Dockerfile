FROM python:3.12-slim

# Install uv
RUN pip install uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml .

# Sync dependencies
RUN uv sync

# Copy the rest of the code
COPY . .

# Expose port
EXPOSE 8000

# Command to run the app
CMD ["uv", "run", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]