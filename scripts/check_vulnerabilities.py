#!/usr/bin/env python3
"""
Check for vulnerabilities in pip-audit JSON report and print details.
"""
import json
import sys
import os


def check_vulnerabilities(report_path: str, service_name: str) -> int:
    """
    Parse pip-audit JSON report and print vulnerability details.
    
    Args:
        report_path: Path to pip-audit-report.json
        service_name: Name of the service being scanned
        
    Returns:
        Exit code (0 if no vulnerabilities, 1 if vulnerabilities found)
    """
    if not os.path.exists(report_path):
        print(f"⚠️  Report file not found: {report_path}")
        return 0
    
    try:
        with open(report_path, 'r') as f:
            data = json.load(f)
        
        # pip-audit JSON format: {'dependencies': [{'name': ..., 'version': ..., 'vulns': [...]}, ...], 'fixes': []}
        vulnerable_packages = []
        count = 0
        
        if isinstance(data, dict) and 'dependencies' in data:
            deps = data['dependencies']
            if isinstance(deps, list):
                for dep in deps:
                    if isinstance(dep, dict):
                        vulns = dep.get('vulns', [])
                        if vulns:
                            name = dep.get('name', 'unknown')
                            version = dep.get('version', 'unknown')
                            count += len(vulns)
                            vulnerable_packages.append({
                                'name': name,
                                'version': version,
                                'vulns': vulns
                            })
        
        if count > 0:
            print(f'⚠️  Found {count} vulnerability/vulnerabilities in {service_name}:')
            print('')
            for pkg in vulnerable_packages:
                print(f'📦 {pkg["name"]}=={pkg["version"]}:')
                for vuln in pkg['vulns']:
                    vuln_id = vuln.get('id', 'N/A')
                    aliases = vuln.get('aliases', [])
                    cve_ids = [a for a in aliases if a.startswith('CVE-')]
                    description = vuln.get('description', 'No description').replace('\r', ' ').strip()
                    fix_versions = vuln.get('fix_versions', [])
                    
                    print(f'  🔴 {vuln_id}', end='')
                    if cve_ids:
                        print(f' ({", ".join(cve_ids)})', end='')
                    print()
                    if description:
                        # Truncate long descriptions
                        desc = description[:200] + '...' if len(description) > 200 else description
                        print(f'     {desc}')
                    if fix_versions:
                        print(f'     Fix: Upgrade to {", ".join(fix_versions)}')
                    print()
            print(f'::warning::Found {count} vulnerabilities in {service_name}')
            return 1
        else:
            print(f'✅ No vulnerabilities found in {service_name}')
            return 0
            
    except json.JSONDecodeError as e:
        print(f'❌ Error parsing JSON report: {e}')
        return 0
    except Exception as e:
        print(f'❌ Error checking vulnerabilities: {e}')
        return 0


if __name__ == '__main__':
    # Get report path and service name from command line arguments
    if len(sys.argv) < 3:
        print("Usage: check_vulnerabilities.py <report_path> <service_name>")
        sys.exit(1)
    
    report_path = sys.argv[1]
    service_name = sys.argv[2]
    
    exit_code = check_vulnerabilities(report_path, service_name)
    sys.exit(exit_code)

