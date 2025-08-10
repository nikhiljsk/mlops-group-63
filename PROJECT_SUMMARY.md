# MLOps Iris Classification Pipeline – Assignment Implementation ✅

## Overview

End-to-end **MLOps pipeline** for Iris flower classification — covering **data versioning, model training, deployment, monitoring, and CI/CD**, with production-ready features and advanced enhancements.

---

## **Part 1: Repository & Data Versioning** ✅

* Professional **GitHub repo** with clean structure, README & architecture diagrams.
* **Data preprocessing** (StandardScaler, train/test split) in `src/preprocess.py`.
* **DVC integration** (`dvc.yaml`, `params.yaml`) for dataset & artifact versioning.
* Maintained **structured directory layout** with clear separation of API, pipeline, tests, data, and frontend.

---

## **Part 2: Model Development & Tracking** ✅

* Trained **5 ML algorithms** (LogisticRegression, RandomForest, SVM, KNN, NaiveBayes) with cross-validation & F1-based best model selection.
* **MLflow** for experiment tracking, metrics, and artifact storage.
* Automated **model registry & serialization** with joblib.

---

## **Part 3: API & Docker Packaging** ✅

* **FastAPI REST API** with `/predict`, `/predict/batch`, `/health`, `/metrics`, `/model/info`, `/retrain`.
* **Dockerized** with multi-stage builds, Compose orchestration & health checks.
* JSON I/O with **Pydantic validation** and batch prediction support.

---

## **Part 4: CI/CD with GitHub Actions** ✅

* **Automated linting & testing** (flake8, pytest, 90%+ coverage).
* **Docker image build & push** to Docker Hub with commit SHA tagging.
* Deployment automation (local scripts & Render-ready configs).

---

## **Part 5: Logging & Monitoring** ✅

* Structured **logging service** with SQLite persistence (`logs.db`).
* **Prometheus /metrics endpoint** with custom ML & system metrics.
* Request/response audit trail with timestamps.

---

## **Part 6: Summary + Demo** ✅

* **PROJECT\_SUMMARY.md** & diagrams in README.
* **Interactive dashboard** & one-command demo setup (`./run_demo.sh`).
* Full **integration test suite** & video walkthrough.

---

## **Bonus & Advanced Features** ✅

* Advanced **Pydantic validation** & error handling.
* **Prometheus + Grafana** integration for real-time monitoring.
* **Live model retraining** via API with hot-reload.
* **Multi-environment deployment** (local, cloud).
* Scalable microservices-ready architecture with security best practices.
