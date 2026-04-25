# 🎮 Tic Tac Toe — Flask + AWS ECR + EKS CI/CD

A production-ready Tic Tac Toe game built with Flask, containerised with Docker,
pushed to Amazon ECR, and deployed to Amazon EKS via GitHub Actions.

---

## Project Structure

```
tictactoe/
├── app/
│   ├── app.py                  # Flask application (game logic + REST API)
│   ├── requirements.txt
│   └── templates/
│       └── index.html          # Single-page UI
├── k8s/
│   ├── 00-namespace.yaml       # Kubernetes namespace
│   ├── 01-deployment.yaml      # Deployment (2 replicas, rolling update)
│   ├── 02-service.yaml         # LoadBalancer Service
│   ├── 03-hpa.yaml             # Horizontal Pod Autoscaler
│   └── 04-secret.yaml          # Secret (docs only — injected by CI)
├── .github/
│   └── workflows/
│       └── ci-cd.yml           # Full CI/CD pipeline
├── Dockerfile                  # Multi-stage build
├── .dockerignore
└── README.md
```

---

## Prerequisites

| Tool | Purpose |
|------|---------|
| AWS CLI v2 | ECR login, EKS kubeconfig |
| eksctl | Create EKS cluster |
| kubectl | Apply manifests |
| Docker | Local build / test |

---

## One-time AWS Setup

### 1 — Create ECR repository

```bash
aws ecr create-repository \
  --repository-name tictactoe \
  --region us-east-1
```

### 2 — Create EKS cluster (if you don't have one)

```bash
eksctl create cluster \
  --name my-cluster \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.small \
  --nodes 2 \
  --nodes-min 2 \
  --nodes-max 4 \
  --managed
```

> ⏳ This takes ~15 minutes.

### 3 — IAM permissions for the GitHub Actions IAM user

The IAM user whose keys you add to GitHub needs at minimum:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:PutImage",
        "ecr:BatchGetImage"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["sts:GetCallerIdentity"],
      "Resource": "*"
    }
  ]
}
```

Also bind the IAM user to the EKS cluster:

```bash
eksctl create iamidentitymapping \
  --cluster my-cluster \
  --region us-east-1 \
  --arn arn:aws:iam::<ACCOUNT_ID>:user/<IAM_USER> \
  --group system:masters \
  --username github-actions
```

---

## GitHub Secrets

Go to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret | Example value |
|--------|--------------|
| `AWS_ACCESS_KEY_ID` | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | `wJalrXUtnFEMI/K7MDENG/...` |
| `AWS_REGION` | `us-east-1` |
| `ECR_REPOSITORY` | `tictactoe` |
| `EKS_CLUSTER_NAME` | `my-cluster` |
| `FLASK_SECRET_KEY` | `$(openssl rand -hex 32)` |

---

## CI/CD Pipeline

```
push to main
     │
     ▼
┌─────────┐     ┌───────────────────┐     ┌──────────────────┐
│  Test   │────▶│  Build & Push ECR │────▶│  Deploy to EKS   │
│  Lint   │     │  Docker image     │     │  kubectl apply   │
│  flake8 │     │  sha + latest tag │     │  rollout status  │
└─────────┘     └───────────────────┘     └──────────────────┘
```

**Job 1 — test**: Runs flake8 linting and any pytest tests on every push/PR.  
**Job 2 — build-and-push**: Builds a multi-stage Docker image, tags it with the Git SHA and `latest`, pushes both to ECR. Runs only on pushes to `main`.  
**Job 3 — deploy**: Updates kubeconfig, recreates the ECR pull secret (tokens expire every 12 h), injects the image URI into the Deployment manifest, applies all k8s manifests, and waits for rollout.

---

## Local Development

```bash
# Run locally with Flask dev server
cd app
pip install -r requirements.txt
FLASK_APP=app.py FLASK_ENV=development flask run

# Build & run the Docker image locally
docker build -t tictactoe:local .
docker run -p 5000:5000 -e SECRET_KEY=dev tictactoe:local
```

Visit `http://localhost:5000`.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Game UI |
| POST | `/api/new-game` | Start a new game (`{"mode":"pvp"\|"pvc"}`) |
| POST | `/api/move` | Make a move (`{"index":0-8}`) |
| GET | `/health` | Health check (used by k8s probes) |

---

## Kubernetes Resources

| Resource | Purpose |
|----------|---------|
| `Namespace` | Isolates all resources under `tictactoe` |
| `Deployment` | 2 replicas, rolling update, non-root security context |
| `Service` | LoadBalancer on port 80 → pod port 5000 |
| `HPA` | Scales 2–6 pods on CPU > 60% or Memory > 75% |
| `Secret` | Flask `SECRET_KEY` injected by CI, never committed |

---

## Accessing the App

After a successful deploy:

```bash
kubectl get svc tictactoe-svc -n tictactoe
# Copy the EXTERNAL-IP / hostname and open it in your browser
```
