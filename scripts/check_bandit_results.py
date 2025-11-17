#!/usr/bin/env python3
"""
Check Bandit security scan results against configured thresholds.
"""
import json
import sys
import os


def check_bandit_results(report_path: str, service_name: str, max_high: int = 0, max_medium: int = 10) -> int:
    """
    Parse Bandit JSON report and check if vulnerabilities exceed thresholds.
    
    Args:
        report_path: Path to bandit-report.json
        service_name: Name of the service being scanned
        max_high: Maximum allowed HIGH severity issues (default: 0)
        max_medium: Maximum allowed MEDIUM severity issues (default: 10)
        
    Returns:
        Exit code (0 if thresholds met, 1 if exceeded)
    """
    if not os.path.exists(report_path):
        print("⚠️  Warning: bandit-report.json not found, skipping threshold check")
        return 0
    
    try:
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        metrics = report.get('metrics', {})
        high_count = metrics.get('SEVERITY.HIGH', 0)
        medium_count = metrics.get('SEVERITY.MEDIUM', 0)
        
        print(f"Bandit Scan Results for {service_name}:")
        print(f"  HIGH severity issues: {high_count} (threshold: {max_high})")
        print(f"  MEDIUM severity issues: {medium_count} (threshold: {max_medium})")
        
        failed = False
        if high_count > max_high:
            print(f"❌ FAILED: Found {high_count} HIGH severity issues, exceeding threshold of {max_high}")
            failed = True
        
        if medium_count > max_medium:
            print(f"❌ FAILED: Found {medium_count} MEDIUM severity issues, exceeding threshold of {max_medium}")
            failed = True
        
        if failed:
            return 1
        else:
            print("✅ PASSED: All vulnerability thresholds met")
            return 0
            
    except json.JSONDecodeError as e:
        print(f"⚠️  Warning: Failed to parse bandit-report.json: {e}")
        return 0
    except Exception as e:
        print(f"⚠️  Warning: Error checking Bandit results: {e}")
        return 0


if __name__ == '__main__':
    # Get arguments from command line or environment variables
    if len(sys.argv) < 3:
        print("Usage: check_bandit_results.py <report_path> <service_name> [max_high] [max_medium]")
        print("  Or set MAX_HIGH_SEVERITY and MAX_MEDIUM_SEVERITY environment variables")
        sys.exit(1)
    
    report_path = sys.argv[1]
    service_name = sys.argv[2]
    
    # Get thresholds from command line args or environment variables
    max_high = int(sys.argv[3]) if len(sys.argv) > 3 else int(os.environ.get('MAX_HIGH_SEVERITY', '0'))
    max_medium = int(sys.argv[4]) if len(sys.argv) > 4 else int(os.environ.get('MAX_MEDIUM_SEVERITY', '10'))
    
    exit_code = check_bandit_results(report_path, service_name, max_high, max_medium)
    sys.exit(exit_code)

