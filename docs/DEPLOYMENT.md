# EcoSight Deployment Guide

## Cloud Deployment & Production Evaluation

This guide covers deploying the EcoSight Wildlife Monitoring system to production and evaluating its performance under real-world conditions.

---

## 📋 Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Local Testing](#local-testing)
3. [Cloud Platform Deployment](#cloud-platform-deployment)
4. [Production Configuration](#production-configuration)
5. [Monitoring & Logging](#monitoring--logging)
6. [Load Testing in Production](#load-testing-in-production)
7. [Scaling Strategies](#scaling-strategies)
8. [Troubleshooting](#troubleshooting)

---

## ✅ Pre-Deployment Checklist

Before deploying to production, ensure:

- [ ] Model artifacts are trained and validated
- [ ] All dependencies are in `requirements.txt`
- [ ] Dockerfiles build successfully
- [ ] Environment variables are configured
- [ ] Health check endpoints are working
- [ ] API documentation is up-to-date
- [ ] Security credentials are not hardcoded
- [ ] Load tests pass locally
- [ ] Backup strategy is defined
- [ ] Monitoring tools are configured

---

## Local Testing

### 1. Test with Docker Compose

```bash
# Build and start all services
docker-compose up -d

# Check container status
docker-compose ps

# View logs
docker-compose logs -f api

# Test API health
curl http://localhost:8000/health

# Test prediction endpoint
curl -X POST http://localhost:8000/predict \
  -F "file=@test_audio.wav"

# Stop all services
docker-compose down
```

### 2. Test with Different Scales

```bash
# Single container
docker-compose up -d --scale api=1
locust -f locustfile.py --host=http://localhost:80 \
  --users=50 --spawn-rate=5 --run-time=2m --headless

# Multiple containers (3)
docker-compose up -d --scale api=3
locust -f locustfile.py --host=http://localhost:80 \
  --users=150 --spawn-rate=15 --run-time=2m --headless

# High scale (5 containers)
docker-compose up -d --scale api=5
locust -f locustfile.py --host=http://localhost:80 \
  --users=250 --spawn-rate=25 --run-time=2m --headless
```

**Expected Results:**

| Scale | Avg Latency | P95 Latency | RPS | Error Rate |
|-------|-------------|-------------|-----|------------|
| 1     | ~500ms      | ~800ms      | 50  | <1%        |
| 3     | ~200ms      | ~350ms      | 150 | <0.5%      |
| 5     | ~150ms      | ~250ms      | 250 | <0.1%      |

---
