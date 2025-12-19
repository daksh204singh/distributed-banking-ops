# Deployment Automation & Canary Strategy

This repo ships an event-driven deployment pipeline that builds Docker images, pushes them to Docker Hub, and rolls them onto the VCL host (`YOUR_PRODUCTION_HOST_IP`) via Ansible. NGINX fronts everything so traffic can gradually shift between the stable release and a canary release for each service.

## Workflow Overview

1. **CI Pipeline** (`.github/workflows/ci.yml`) runs on every push/PR. When `main` goes green, GitHub automatically triggers **Deploy Banking Services** (`deploy.yml`) via `workflow_run`.
2. The deploy workflow:
   - Builds account-service and transaction-service images from the merge commit.
   - Pushes both `latest` and `<short-sha>` tags to Docker Hub.
   - Uses Ansible to install Docker (if missing), run Postgres + RabbitMQ, and start **two copies** of each service:
     - `*-stable` containers run the last known good tag.
     - `*-canary` containers run the new tag.
   - Renders an NGINX config that proxies `/account/*` and `/transaction/*` and splits traffic between the stable and canary instances based on the requested weight.
3. Manual dispatch of the workflow exposes inputs for `canary_weight`, `enable_canary`, and `promote_canary`, enabling controlled experiments and promotions.

## Required GitHub Secrets

| Secret                                                                                                        | Purpose                                                        |
| ------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN`                                                                  | Push images to your Docker Hub namespace.                      |
| `ANSIBLE_HOST`                                                                                              | (Optional) Target host override. Defaults to `YOUR_PRODUCTION_HOST_IP`. |
| `ANSIBLE_USER`                                                                                              | SSH user on the production VM.                                 |
| `ANSIBLE_PRIVATE_KEY`                                                                                       | PEM-formatted private key for the user above.                  |
| `ANSIBLE_BECOME_PASSWORD`                                                                                   | (Optional) sudo password if required.                          |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`                                                     | Injected into Postgres and used in `DATABASE_URL`.           |
| `RABBITMQ_USER`, `RABBITMQ_PASSWORD`, `RABBITMQ_QUEUE`, `RABBITMQ_PORT`, `RABBITMQ_MANAGEMENT_PORT` | Configure RabbitMQ containers and application env.             |

> Secrets omitted here fall back to the defaults defined in `ansible/roles/banking_app/defaults/main.yml`.

## Canary Controls

- **Stable tag tracking** – the host stores the currently promoted tag in `/etc/banking/releases/stable_tag`. Ansible falls back to `latest` if the file does not exist.
- **New deployments** push the new tag into the *canary* containers and leave the stable containers on the recorded tag. The default canary weight is 10%.
- **Automated health gates** – after the canary containers start, Ansible probes `http://127.0.0.1:8100/health` and `:8101/health`. If either fails, their logs are copied to `/var/log/banking/canary_failures/`, traffic is returned to the stable release, the canary containers are removed, and the workflow fails so you can inspect the breadcrumbs.
- **Manual workflow dispatch** inputs:
  - `canary_weight` (0–100) – how much traffic to send to the canary.
  - `enable_canary` – set to `false` to skip canary containers entirely.
  - `promote_canary` – set to `true` to make the current canary tag the new stable tag; promotion automatically shifts 100% of traffic to the canary, recreates the stable containers on ports 8000/8001, then retires the canary slot.
- **NGINX gateway** – exposed on host port 80. Clients should call:
  - `http://YOUR_PRODUCTION_HOST_IP/account/health` (proxied to account service)
  - `http://YOUR_PRODUCTION_HOST_IP/transaction/health`
  - `http://YOUR_PRODUCTION_HOST_IP/healthz` (NGINX self-check)

  The legacy ports (8000/8001/8100/8101) remain published for troubleshooting but end-users should rely on port 80.

## Manual Deployment

When a manual rollout is needed, run the steps below from the repo root so the bundled `ansible.cfg` is honored.

1. Build/push images (optional – CI usually does this automatically):
   ```bash
   ./scripts/build-images.sh <tag> <dockerhub-username>
   docker push <dockerhub-username>/account-service:<tag>
   docker push <dockerhub-username>/transaction-service:<tag>
   ```
2. Run the playbook (still from the repo root):
   ```bash
   ansible-playbook \
     -i ansible/inventory/hosts.ini \
     -u "$ANSIBLE_USER" \
     --private-key ~/.ssh/id_rsa \
     -e "dockerhub_username=$DOCKERHUB_USERNAME" \
     -e "dockerhub_password=$DOCKERHUB_TOKEN" \
     -e "canary_tag=<tag>" \
     -e "canary_traffic_percentage=10" \
     -e "enable_canary=true" \
     -e "promote_canary=false" \
     ansible/playbooks/deploy.yml
   ```

   Add `-e "promote_canary=true"` to promote the canary tag to stable during the same run, or `-e "enable_canary=false"` for an all-stable rollout.

## Post-Deployment Validation

1. Verify containers:
   ```bash
   ssh YOUR_SSH_USER@YOUR_PRODUCTION_HOST_IP
   docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
   ```

Expect to see the following containers:

- `banking-account-service-stable`
- `banking-account-service-canary`
- `banking-transaction-service-stable`
- `banking-transaction-service-canary`
- `banking-postgres`
- `banking-rabbitmq`
- `banking-gateway`
- `banking-loki`
- `banking-promtail`

2. Hit the public endpoints (through NGINX):
   ```bash
   curl http://YOUR_PRODUCTION_HOST_IP/account/health
   curl http://YOUR_PRODUCTION_HOST_IP/transaction/health
   curl http://YOUR_PRODUCTION_HOST_IP/healthz
   ```
3. Inspect logs for the new containers if required:
   ```bash
   docker logs banking-account-service-canary --tail 50
   docker logs banking-transaction-service-canary --tail 50
   ```

## Troubleshooting

- **Docker permissions on the runner** – the self-hosted runner still needs Docker + group membership; restart `./run.sh` after changing groups.
- **SSH access** – TCP/22 must stay open from the runner (`YOUR_RUNNER_IP`) to the host (`YOUR_PRODUCTION_HOST_IP`). Sanity-check with `ssh YOUR_SSH_USER@YOUR_PRODUCTION_HOST_IP`.
- **Tag mismatch** – if services restart with “password authentication failed”, either reset the Postgres volume or update the `POSTGRES_*` secrets to match the DB credentials on disk.
- **Canary rollback** – when the canary fails its health checks, the workflow exits with an error but the stable release stays online. Inspect `/var/log/banking/canary_failures/` for the captured logs + JSON summary before re-running with a fix.
