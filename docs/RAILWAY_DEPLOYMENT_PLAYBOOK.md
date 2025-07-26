# Deployment & Release Procedures for Railway Deployments

## Environment Setup

1. **Connect GitHub Repository**
   - Integrate your GitHub repository with Railway for automated deployments.

2. **Environment Variables**
   - Manage environmental secrets securely in the Railway dashboard.
   - Use environment variables for sensitive data, such as `API_KEYS` and `DATABASE_URL`.

3. **Volume Creation**
   - Use Railway volumes for persistent data storage:

     ```bash
     railway volumes create gary-zero-data --size 10
     ```

## Variable Injection

- Ensure all sensitive configurations are passed as environment variables.
- For example, when using Python with FastAPI:

  ```python
  import os
  from fastapi import FastAPI

  app = FastAPI()

  @app.get("/health")
  def read_health():
      return {"status": "ok"}

  if __name__ == "__main__":
      port = int(os.getenv("PORT", 8000))
      uvicorn.run(app, host="0.0.0.0", port=port)
  ```

## Port Binding

- Bind to the port provided by Railway environment:

  ```bash
  PORT=${PORT-8000}
  ```

## Health Checks

- Configure application health checks

## Rollbacks

1. **Manual Rollback**
   - Use Railway's UI or CLI to deploy a previous commit.

2. **Automatic Rollback**
   - Configure retry and rollback policies in `railpack.json`:

     ```json
     "restartPolicyType": "ON_FAILURE",
     "restartPolicyMaxRetries": 3
     ```

## Canary Deployment Strategy

1. **Feature Branch Deployment**
   - Deploy feature branches to isolated environments for testing.

2. **Gradual Rollout**
   - Gradually increase traffic to the new deployment and monitor performance and metrics.

## CI Workflow YAML Example

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ "main", "develop" ]
  pull_request:
    branches: [ "main", "develop" ]
  workflow_dispatch:

env:
  PYTHON_VERSION: "3.13"

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Test
        run: |
          pytest

  deploy-to-railway:
    runs-on: ubuntu-latest
    needs: build-and-test
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Railway
        run: |
          railway up
```

## Smoke-Test Scripts

- Example Python script to smoke test a deployment:

  ```python
  import requests

  response = requests.get('https://your-railway-domain.up.railway.app/health')
  assert response.status_code == 200
  assert response.json() == {"status": "ok"}
  ```
