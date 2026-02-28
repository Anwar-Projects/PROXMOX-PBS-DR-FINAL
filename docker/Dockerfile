FROM python:3.11-slim

LABEL maintainer="Proxmox DR Team"
LABEL description="Proxmox PBS Disaster Recovery Orchestration"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    proxmox-backup-client \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy Python requirements
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/proxmox_dr/ ./proxmox_dr/

# Copy scripts
COPY scripts/ ./scripts/
RUN chmod +x ./scripts/*.sh

# Create necessary directories
RUN mkdir -p /etc/proxmox-dr /var/lib/proxmox-dr/recovery

# Copy default config
COPY config/config.yaml.example /etc/proxmox-dr/config.yaml.example

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from proxmox_dr import __version__; print(__version__)" || exit 1

# Default command
ENTRYPOINT ["python", "-m", "proxmox_dr"]
CMD ["--help"]
