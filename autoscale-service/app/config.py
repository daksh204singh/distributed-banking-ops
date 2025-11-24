"""Configuration for autoscaling service."""
import os

# Service name mapping from Prometheus job to Docker container name prefix
SERVICE_MAP = {
    'account-service': 'banking-account-service',
    'transaction-service': 'banking-transaction-service'
}

# Reverse mapping from container prefix to service name (for network aliases)
CONTAINER_TO_SERVICE = {v: k for k, v in SERVICE_MAP.items()}

# Scaling limits
MIN_INSTANCES = int(os.getenv('MIN_INSTANCES', '1'))
MAX_INSTANCES = int(os.getenv('MAX_INSTANCES', '5'))

# Cooldown period in minutes (prevent rapid scaling)
SCALING_COOLDOWN_MINUTES = int(os.getenv('SCALING_COOLDOWN_MINUTES', '5'))

# Docker network name (from Ansible defaults)
DOCKER_NETWORK = os.getenv('DOCKER_NETWORK', 'banking-network')

# Docker command timeout in seconds
DOCKER_TIMEOUT = int(os.getenv('DOCKER_TIMEOUT', '60'))

# Container stop timeout in seconds
CONTAINER_STOP_TIMEOUT = int(os.getenv('CONTAINER_STOP_TIMEOUT', '30'))

# Docker query timeout in seconds (for ps, inspect commands)
DOCKER_QUERY_TIMEOUT = int(os.getenv('DOCKER_QUERY_TIMEOUT', '10'))

