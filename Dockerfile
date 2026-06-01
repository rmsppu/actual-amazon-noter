FROM python:3.11-alpine

WORKDIR /app

# Install build dependencies if needed, then copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Inject compile-time Git commit hash
ARG COMMIT_HASH=unknown
RUN if [ -d .git ]; then \
      apk add --no-cache git && \
      git rev-parse --short HEAD > commit_hash.txt && \
      apk del git; \
    elif [ "$COMMIT_HASH" != "unknown" ]; then \
      echo "$COMMIT_HASH" > commit_hash.txt; \
    else \
      echo "unknown" > commit_hash.txt; \
    fi

ARG VERSION=unknown
ENV APP_VERSION=$VERSION


# Ensure the python script is executable
RUN chmod +x actual-ecommerce-noter

EXPOSE 8080

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

CMD ["gunicorn", "-w", "2", "-t", "300", "-b", "0.0.0.0:8080", "app:app"]
