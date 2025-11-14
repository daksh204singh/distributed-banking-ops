# distributed-banking-ops

## Overview
This project implements an event-driven CI/CD pipeline for a distributed banking application. Banking workloads demand real-time responsiveness, high fault-tolerance, and dynamic scaling, especially during traffic surges like Black Friday. Our pipeline automates testing, secure deployment, and continuous monitoring to ensure reliability, rapid yet safe delivery, and efficient infrastructure utilization.

By combining GitHub Actions, Docker, Ansible, Prometheus, Grafana, Loki, and automated scaling scripts, this system simulates a production-grade DevOps environment designed for mission-critical financial services.

Deployment automation, canary strategy details, and manual run instructions are documented in `docs/deployment.md`.

## Key Deliverables
- **Repository & Branch Protection**: Feature branches, PR workflows, protected release branch.
- **Automated CI Pipeline**: Linting, unit tests, integration tests, and security scans.
- **Test Environment Provisioning**: On-demand test containers & automated load testing.
- **Canary Deployment System**: Gradual rollout via NGINX and Ansible.
- **Load Balancing**: NGINX-based traffic routing across microservice instances.
- **Auto-Scaling Simulation**: Scale-out and scale-in containers driven by metrics thresholds.
- **Monitoring & Observability Stack**: Prometheus + Grafana dashboards, Loki logs, alerts.
- **Notifications & Rollback Mechanisms**: PR feedback, deployment alerts, automated rollback.

## 

### Team Members
- **YOUR_SSH_USER**
  - **Production Deployment & Release Automation**:
    - Develop and maintain Ansible playbooks for production deployment (not test).
    - Build and manage production-ready Docker images and registry pushes.
  - **Load Balancing & Canary Deployment**:
    - Configure NGINX-based load balancing across app instances.
    - Implement canary deployment logic with gradual traffic migration and automated rollback.
  - **Release Branch Management**
    - Enforce branch protection rules, manual review, and approval-gated release process.

- **YOUR_SSH_USER**
  - **Monitoring & Auto-Scaling**
    - Deploy and configure Prometheus, Grafana, and Loki for metrics, dashboards, and logs.
    - Set alert rules and webhook triggers for real-time scaling decisions.
    - Build auto-scaling script to programmatically start/stop containers based on CPU load.
  - **System Health & Alerting**
    - Configure alerting pipeline (email/webhook) and predictive scaling behavior.

- ****
  - **Automated Testing & CI**
    - Configure GitHub Actions pipeline for linting, unit tests, integration tests, and security scanning.
    - Maintain test suite and enforce test coverage requirements.
  - **Load Testing & CI Environment**
    - Implement load-test stage and teardown automation inside CI pipeline.
    - Develop Ansible playbooks for test environment provisioning and cleanup.
  - **PR Feedback Automation**
    - Ensure test, lint, and security logs surface back into GitHub PR for developer insights.

> **Note:** While specific deliverables are assigned, all team members will actively contribute technical expertise across the project to ensure robust integration and quality outcomes.
