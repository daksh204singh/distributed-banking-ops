"""Auto-scaling service logic."""
import subprocess
from typing import Optional
from app.schemas import WebhookPayload
from app.config import SERVICE_MAP, CONTAINER_TO_SERVICE, MIN_INSTANCES, MAX_INSTANCES, DOCKER_NETWORK, DOCKER_TIMEOUT, CONTAINER_STOP_TIMEOUT
from app.helpers import (
    can_scale,
    record_scaling_action,
    get_container_count,
    get_base_container_info,
    get_existing_container_numbers
)


def process_webhook_alerts(payload: WebhookPayload) -> dict:
    """Process webhook alerts and trigger scaling actions.
    
    Args:
        payload: Webhook payload from Grafana
    
    Returns:
        Dictionary with processing results
    """
    results = []
    
    for alert in payload.alerts:
        if alert.status != 'firing':
            continue
        
        service = alert.labels.service or alert.labels.job or ''
        alertname = alert.labels.alertname or ''
        
        if not service:
            continue
        
        # Map service names to container name prefix
        container_prefix = SERVICE_MAP.get(service, f'banking-{service}')
        
        # Determine action
        action = determine_scaling_action(alertname)
        if not action:
            continue
        
        # Process scaling
        try:
            result = scale_service(container_prefix, action)
            results.append({
                'service': service,
                'action': action,
                'success': result['success'],
                'message': result.get('message', '')
            })
        except Exception as e:
            results.append({
                'service': service,
                'action': action,
                'success': False,
                'message': str(e)
            })
    
    return {'results': results, 'status': 'ok'}


def scale_service(container_prefix: str, action: str) -> dict:
    """Scale a service up or down.
    
    Args:
        container_prefix: Container name prefix (e.g., 'banking-account-service')
        action: 'scale_up' or 'scale_down'
    
    Returns:
        Dictionary with success status and message
    
    Raises:
        Exception: If scaling fails
    """
    # Check cooldown period
    if not can_scale(container_prefix, action):
        return {
            'success': False,
            'message': f'Skipping {action} for {container_prefix}: cooldown period active'
        }
    
    current = get_container_count(container_prefix)
    new_count = min(current + 1, MAX_INSTANCES) if action == 'scale_up' else max(current - 1, MIN_INSTANCES)
    
    # Idempotency check: already at target count
    if new_count == current:
        return {
            'success': False,
            'message': f'Skipping {action} for {container_prefix}: already at target count {current}'
        }
    
    # Perform scaling
    if action == 'scale_up':
        scale_up(container_prefix, new_count)
    else:
        scale_down(container_prefix, new_count)
    
    # Record scaling action timestamp
    record_scaling_action(container_prefix, action)
    
    return {
        'success': True,
        'message': f'Successfully {action} {container_prefix} from {current} to {new_count}'
    }


def scale_up(container_prefix: str, target_count: int):
    """Scale up by creating new containers.
    
    Args:
        container_prefix: Container name prefix (e.g., 'banking-account-service')
        target_count: Target number of containers
    
    Raises:
        Exception: If scaling fails
    """
    try:
        # Get base container info
        base_info = get_base_container_info(container_prefix)
        
        # Get existing container numbers
        existing_numbers = get_existing_container_numbers(container_prefix)
        
        # Find the next available number
        next_number = 1
        numbered_containers = [n for n in existing_numbers if n is not None]
        while next_number in numbered_containers:
            next_number += 1
        
        new_container_name = f"{container_prefix}-{next_number}"
        
        # Build docker run command
        cmd = ['docker', 'run', '-d']
        
        # Container name
        cmd.extend(['--name', new_container_name])
        
        # Network
        cmd.extend(['--network', DOCKER_NETWORK])
        
        # Add network alias for load balancing (e.g., account-service)
        # This allows nginx to discover all instances via DNS
        service_name = CONTAINER_TO_SERVICE.get(container_prefix, container_prefix.replace('banking-', ''))
        cmd.extend(['--network-alias', service_name])
        
        # Restart policy
        if base_info['restart_policy'] != 'no':
            cmd.extend(['--restart', base_info['restart_policy']])
        
        # Environment variables
        for env_var in base_info['env']:
            cmd.extend(['-e', env_var])
        
        # Labels (copy from base container)
        for key, value in base_info['labels'].items():
            cmd.extend(['--label', f'{key}={value}'])
        
        # Add a label to identify this as a scaled instance
        cmd.extend(['--label', 'scaled-instance=true'])
        
        # Image
        cmd.append(base_info['image'])
        
        # Execute docker run
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=DOCKER_TIMEOUT)
        print(f"Scaled up {container_prefix}: created {new_container_name}")
        
    except subprocess.CalledProcessError as e:
        raise Exception(f"Docker run failed: {e.stderr}")
    except Exception as e:
        raise Exception(f"Scale up failed: {e}")


def scale_down(container_prefix: str, target_count: int):
    """Scale down by stopping and removing the highest numbered container.
    
    Args:
        container_prefix: Container name prefix (e.g., 'banking-account-service')
        target_count: Target number of containers
    
    Raises:
        Exception: If scaling fails
    """
    try:
        # Get existing container numbers
        existing_numbers = get_existing_container_numbers(container_prefix)
        
        if not existing_numbers:
            print(f"No containers found to scale down for {container_prefix}")
            return
        
        # Find the highest numbered container (not the base container)
        numbered_containers = [n for n in existing_numbers if n is not None]
        if not numbered_containers:
            print(f"No numbered containers found to scale down for {container_prefix}")
            return
        
        # Remove the highest numbered container
        highest_number = max(numbered_containers)
        container_to_remove = f"{container_prefix}-{highest_number}"
        
        # Stop and remove container
        subprocess.run(['docker', 'stop', container_to_remove], check=True, timeout=CONTAINER_STOP_TIMEOUT)
        subprocess.run(['docker', 'rm', container_to_remove], check=True, timeout=CONTAINER_STOP_TIMEOUT)
        
        print(f"Scaled down {container_prefix}: removed {container_to_remove}")
        
    except subprocess.CalledProcessError as e:
        raise Exception(f"Docker stop/rm failed: {e.stderr}")
    except Exception as e:
        raise Exception(f"Scale down failed: {e}")


def determine_scaling_action(alertname: str) -> Optional[str]:
    """Determine scaling action from alert name.
    
    Args:
        alertname: Name of the Grafana alert
    
    Returns:
        'scale_up', 'scale_down', or None
    """
    alertname_lower = alertname.lower()
    
    if 'scale_up' in alertname_lower or 'high' in alertname_lower:
        return 'scale_up'
    elif 'scale_down' in alertname_lower or 'low' in alertname_lower:
        return 'scale_down'
    
    return None


def map_service_name(prometheus_job: str) -> str:
    """Map Prometheus job name to Docker container name prefix.
    
    Args:
        prometheus_job: Job name from Prometheus/Grafana (e.g., 'account-service')
    
    Returns:
        Docker container name prefix (e.g., 'banking-account-service')
    """
    return SERVICE_MAP.get(prometheus_job, f'banking-{prometheus_job}')
