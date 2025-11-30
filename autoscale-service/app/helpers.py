"""Helper functions for autoscaling operations."""
import json
import subprocess
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.config import SCALING_COOLDOWN_MINUTES, DOCKER_NETWORK, DOCKER_QUERY_TIMEOUT

# Track last scaling action per service and action type
_last_scaling_actions: Dict[str, datetime] = {}


def can_scale(container_prefix: str, action: str) -> bool:
    """Check if enough time has passed since last scaling action (cooldown check).
    
    Args:
        container_prefix: Container name prefix (e.g., 'banking-account-service')
        action: 'scale_up' or 'scale_down'
    
    Returns:
        True if scaling is allowed, False if cooldown period is active
    """
    key = f"{container_prefix}:{action}"
    last_action = _last_scaling_actions.get(key)
    
    if last_action is None:
        return True  # No previous action, allow scaling
    
    time_since_last = datetime.now() - last_action
    cooldown = timedelta(minutes=SCALING_COOLDOWN_MINUTES)
    
    if time_since_last < cooldown:
        remaining = cooldown - time_since_last
        print(f"Cooldown active for {container_prefix} {action}: {remaining.seconds}s remaining")
        return False
    
    return True


def record_scaling_action(container_prefix: str, action: str):
    """Record the timestamp of a scaling action."""
    key = f"{container_prefix}:{action}"
    _last_scaling_actions[key] = datetime.now()
    print(f"Recorded {action} action for {container_prefix} at {datetime.now()}")


def get_container_count(container_prefix: str) -> int:
    """Get current container count for a service.
    
    Looks for containers matching the prefix pattern:
    - banking-account-service (base container)
    - banking-account-service-1, banking-account-service-2, etc. (scaled instances)
    
    Args:
        container_prefix: Container name prefix (e.g., 'banking-account-service')
    
    Returns:
        Number of running containers for the service
    """
    try:
        # Get all containers with the prefix in their name
        result = subprocess.run(
            ['docker', 'ps', '--filter', f'name={container_prefix}', '--format', '{{.Names}}'],
            capture_output=True,
            text=True,
            check=True,
            timeout=DOCKER_QUERY_TIMEOUT
        )
        containers = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        
        # Count containers that match the pattern (base or numbered instances)
        count = 0
        for container in containers:
            # Match base container (exact match) or numbered instances (prefix-N)
            if container == container_prefix or re.match(rf'^{re.escape(container_prefix)}-\d+$', container):
                count += 1
        
        return count if count > 0 else 1  # Default to 1 if no containers found
    except Exception as e:
        print(f"Error getting container count: {e}")
        return 1


def get_base_container_info(container_prefix: str) -> dict:
    """Get image, environment variables, and other config from the base container.
    
    Args:
        container_prefix: Container name prefix (e.g., 'banking-account-service')
    
    Returns:
        Dictionary with container configuration (image, env, labels, restart_policy, port_bindings)
    
    Raises:
        Exception: If base container not found or inspect fails
    """
    try:
        # First, try to find the base container (exact name match)
        result = subprocess.run(
            ['docker', 'ps', '--filter', f'name=^{container_prefix}$', '--format', '{{.Names}}'],
            capture_output=True,
            text=True,
            check=True,
            timeout=DOCKER_QUERY_TIMEOUT
        )
        base_container = result.stdout.strip()
        
        # If base container not found, try to find any numbered instance
        if not base_container:
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name={container_prefix}', '--format', '{{.Names}}'],
                capture_output=True,
                text=True,
                check=True,
                timeout=DOCKER_QUERY_TIMEOUT
            )
            containers = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            if containers:
                base_container = containers[0]
        
        if not base_container:
            raise Exception(f"No base container found for {container_prefix}")
        
        # Get container inspect info
        inspect_result = subprocess.run(
            ['docker', 'inspect', base_container],
            capture_output=True,
            text=True,
            check=True,
            timeout=DOCKER_QUERY_TIMEOUT
        )
        container_info = json.loads(inspect_result.stdout)[0]
        
        # Extract image
        image = container_info['Config']['Image']
        
        # Extract environment variables
        env_vars = container_info['Config']['Env'] or []
        
        # Extract labels
        labels = container_info['Config']['Labels'] or {}
        
        # Extract restart policy
        restart_policy = container_info['HostConfig']['RestartPolicy']['Name']
        
        # Extract port mappings (if any)
        port_bindings = container_info['HostConfig']['PortBindings'] or {}
        
        return {
            'image': image,
            'env': env_vars,
            'labels': labels,
            'restart_policy': restart_policy,
            'port_bindings': port_bindings
        }
    except Exception as e:
        raise Exception(f"Failed to get base container info: {e}")


def get_existing_container_numbers(container_prefix: str) -> List[Optional[int]]:
    """Get list of existing container numbers (None for base container, int for numbered).
    
    Args:
        container_prefix: Container name prefix (e.g., 'banking-account-service')
    
    Returns:
        List of container numbers (None for base, int for numbered instances)
    """
    try:
        result = subprocess.run(
            ['docker', 'ps', '--filter', f'name={container_prefix}', '--format', '{{.Names}}'],
            capture_output=True,
            text=True,
            check=True,
            timeout=DOCKER_QUERY_TIMEOUT
        )
        containers = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        
        numbers = []
        for container in containers:
            if container == container_prefix:
                # Base container
                numbers.append(None)
            else:
                # Numbered container - extract number
                match = re.match(rf'^{re.escape(container_prefix)}-(\d+)$', container)
                if match:
                    numbers.append(int(match.group(1)))
        
        return numbers
    except Exception as e:
        print(f"Error getting container numbers: {e}")
        return []

