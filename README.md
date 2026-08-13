<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:7F00FF,100:E100FF&height=200&section=header&text=PredictV&fontSize=70&fontColor=ffffff&animation=fadeIn&fontAlignY=35&desc=Petrol%20Motorbike%20ML%20Prediction%20Toolkit%20%26%20FastAPI%20Backend&descSize=20&descAlignY=55&descColor=f3e5f5" width="100%" />

<br/>

[![License: MIT](https://img.shields.io/badge/License-MIT-7F00FF.svg?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.5-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org/)

<br/>

**A Python Machine Learning toolkit for petrol motorbike emission prediction, engine health scoring, and predictive maintenance.**
**Powered by a high-performance FastAPI backend with JWT auth, multi-model support, and explainable AI.**

[📖 API Documentation](#-api-endpoints) · [🐛 Report Bug](https://github.com/ShelumHansana/PredictV/issues) · [✨ Request Feature](https://github.com/ShelumHansana/PredictV/issues)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Screenshots](#-screenshots)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [Usage](#-usage)
- [API Endpoints](#-api-endpoints)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)
- [Acknowledgments](#-acknowledgments)

---

## 🔍 Overview

**PredictV** is a specialised machine learning platform designed for petrol-powered motorbikes. It builds, trains, evaluates, and serves ML models for emission analysis, engine health scoring, fault detection, and predictive maintenance. It provides a modular Python toolkit for experiments alongside an asynchronous REST API backend for production deployments.

### 🎯 Problem Statement

Machine learning for motorbike diagnostics often suffers from:
- Repetitive boilerplate code for data loading and feature transformation
- Friction when transitioning models from notebook experiments to production APIs
- Lack of interpretability and transparency in predictions
- Complex setup requirements for serving multi-algorithm predictions
- Generic vehicle models that don't account for motorbike-specific emission patterns

### 💡 Solution

PredictV solves these challenges with:
- **Petrol Motorbike Focus** — Trained exclusively on petrol motorbike emission data for accurate, domain-specific predictions
- **Unified Python Pipeline** supporting scikit-learn, XGBoost, LightGBM, and CatBoost
- **Production-Ready REST API** built with FastAPI, JWT authentication, and OpenAPI documentation
- **Explainable AI Integration** using SHAP and LIME to generate interpretability insights
- **Automated PDF Reports** for model performance and evaluation tracking

---

## ✨ Features

<div align="center">

| 🤖 **ML Toolkit** | 🚀 **FastAPI Backend** |
|---|---|
| Multi-algorithm support (sklearn, XGBoost, LightGBM, CatBoost) | Asynchronous RESTful API endpoints |
| Automated feature engineering & preprocessing | Secure JWT authentication & role management |
| Hyperparameter tuning & cross-validation | PostgreSQL & SQLite database support |
| Model persistence (`.joblib` serialization) | Automatic OpenAPI & Redoc documentation |

| 📊 **Explainable AI** | 📄 **Reporting & Alerts** |
|---|---|
| SHAP feature importance visualizations | Auto-generated PDF evaluation reports |
| LIME local prediction explanations | Email notifications via SMTP |
| Model metrics tracking & ROC curve plots | YAML-based reproducible experiment configs |

</div>

### Key Highlights

- 🤖 **Multi-Model Support** — Seamlessly train and compare Random Forest, XGBoost, LightGBM, and CatBoost
- 📊 **Explainable AI (XAI)** — Integrated SHAP values and LIME explanations for trusted predictions
- 🚀 **FastAPI Backend** — High-performance async service with automated Swagger interactive docs
- 🔐 **Secure Auth** — Token-based JWT authentication with hashed password verification
- 📈 **Automated Preprocessing** — Built-in pipelines for scaling, encoding, and feature selection
- 📄 **PDF Report Generation** — Export comprehensive evaluation summaries via ReportLab
- ⚙️ **Reproducible Configs** — Experiment parameterization via declarative YAML files

---

## 🛠️ Tech Stack

<div align="center">

| Layer | Technology | Purpose |
|---|---|---|
| **Language** | ![Python](https://img.shields.io/badge/Python_3.9+-3776AB?style=flat-square&logo=python&logoColor=white) | Core programming language |
| **API Framework** | ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white) | High-performance REST API |
| **ASGI Server** | ![Uvicorn](https://img.shields.io/badge/Uvicorn-2C2C2C?style=flat-square&logo=uvicorn&logoColor=white) | Asynchronous web server |
| **ML Core** | ![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=flat-square&logo=scikitlearn&logoColor=white) | Core ML algorithms & pipeline |
| **Boosting** | ![XGBoost](https://img.shields.io/badge/XGBoost_+_LightGBM_+_CatBoost-006CBF?style=flat-square) | Advanced gradient boosting |
| **Explainability** | ![SHAP](https://img.shields.io/badge/SHAP_+_LIME-7F00FF?style=flat-square) | Model interpretability & feature impact |
| **Database** | ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white) | Relational database storage |
| **ORM** | ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy_2.0-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white) | Async ORM database access |
| **Data Processing** | ![Pandas](https://img.shields.io/badge/Pandas_+_NumPy-150458?style=flat-square&logo=pandas&logoColor=white) | Data manipulation & analytics |
| **Authentication** | ![JWT](https://img.shields.io/badge/JWT_Auth-000000?style=flat-square&logo=jsonwebtokens&logoColor=white) | User session & route protection |
| **PDF Engine** | ![ReportLab](https://img.shields.io/badge/ReportLab-CC0000?style=flat-square) | Dynamic PDF report generation |
| **Testing & Linting** | ![Pytest](https://img.shields.io/badge/Pytest_+_Ruff-0A9EDC?style=flat-square&logo=pytest&logoColor=white) | Test suite & code quality |

</div>

---

## 🏗️ Architecture

```mermaid
graph TB
    subgraph Client["🖥️ Application Clients"]
        CLI["CLI Tool (predictv)"]
        WebApp["Web App / External Clients"]
    end

    subgraph API["🚀 FastAPI Backend"]
        Router["API v1 Routers"]
        Auth["JWT Authentication"]
        Services["Service Layer"]
        Schemas["Pydantic Schemas"]
    end

    subgraph ML["🤖 Machine Learning Pipeline"]
        FE["Feature Engineer"]
        Trainer["Model Trainer"]
        Eval["Evaluator"]
        XAI["SHAP & LIME Engine"]
    end

    subgraph Data["💾 Persistence Layer"]
        DB["PostgreSQL / SQLite"]
        Storage["Saved Models (.joblib)"]
        Reports["PDF Reports"]
    end

    WebApp --> Router
    CLI --> ML
    Router --> Auth
    Auth --> Services
    Services --> ML
    Services --> DB
    ML --> FE
    FE --> Trainer
    Trainer --> Eval
    Trainer --> XAI
    Trainer --> Storage
    Eval --> Reports
    Schemas --> Router
```

---

## 📸 Screenshots

> **📌 Coming Soon** — Screenshots of interactive API docs and sample evaluation reports will be added here.

<!--
Uncomment and add your screenshots:

<div align="center">
<img src="screenshots/api-docs.png" width="45%" />
<img src="screenshots/shap-plot.png" width="45%" />
</div>
-->

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.9+**
- **Git**
- **PostgreSQL** (Optional; SQLite is supported for local development)

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/ShelumHansana/PredictV.git
cd PredictV
```

#### 2. Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate      # Windows
# source .venv/bin/activate # macOS/Linux
```

#### 3. Install ML Toolkit

```bash
pip install -e ".[dev]"
```

#### 4. Set Up FastAPI Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
```

#### 5. Launch Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be live at `http://localhost:8000`  
Swagger documentation available at `http://localhost:8000/docs`

---

## 🔑 Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Server Configuration
PROJECT_NAME="PredictV API"
API_V1_STR="/api/v1"

# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./predictv.db
# For PostgreSQL:
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/predictv_db

# Security & Authentication
SECRET_KEY=your_super_secret_jwt_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Email Notifications (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

---

## 💻 Usage

### Python Toolkit Example

```python
from predictv.features import FeatureEngineer
from predictv.training import Trainer

# Initialize pipeline
engineer = FeatureEngineer()
X_train, X_test, y_train, y_test = engineer.prepare("data/raw/dataset.csv", target="target_column")

# Train model
trainer = Trainer(model_type="random_forest", random_state=42)
model = trainer.fit(X_train, y_train)

# Evaluate results
report = trainer.evaluate(X_test, y_test)
print(report)
```

### CLI Command Example

```bash
# Train from YAML config
predictv train --config configs/experiment.yaml

# Evaluate saved model
predictv evaluate --model ml_models/model.joblib --data data/raw/dataset.csv
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/auth/login` | Authenticate user & obtain JWT token | ❌ No |
| `POST` | `/api/v1/auth/register` | Register new user account | ❌ No |
| `GET` | `/api/v1/predictions` | Retrieve list of prediction records | ✅ Yes |
| `POST` | `/api/v1/predictions` | Run new model prediction | ✅ Yes |
| `GET` | `/api/v1/predictions/{id}` | Fetch specific prediction details | ✅ Yes |
| `GET` | `/api/v1/models` | List available trained models | ✅ Yes |
| `POST` | `/api/v1/models/train` | Trigger new model training job | ✅ Yes |
| `GET` | `/api/v1/reports` | List generated evaluation reports | ✅ Yes |
| `GET` | `/api/v1/reports/{id}/pdf` | Download PDF evaluation report | ✅ Yes |

---

## 📁 Project Structure

```
PredictV/
├── configs/                    # YAML experiment configurations
│   └── experiment.yaml
├── data/                       # Datasets
│   ├── raw/
│   └── processed/
├── src/predictv/               # 📦 Core ML Python Package
│   ├── __init__.py
│   ├── cli.py                  # CLI command runner
│   ├── features.py             # Feature engineering module
│   └── training.py             # Training & evaluation pipeline
├── backend/                    # 🚀 FastAPI Backend Application
│   ├── app/
│   │   ├── api/                # API routes & versioning
│   │   │   └── v1/
│   │   ├── ml/                 # ML integration layer
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic validation schemas
│   │   ├── services/           # Business logic layer
│   │   ├── reports/            # PDF report generator
│   │   ├── utils/              # Helper utilities
│   │   ├── config.py           # Application settings
│   │   ├── database.py         # Database session & engine
│   │   └── main.py             # FastAPI entry point
│   ├── ml_models/              # Serialized model store
│   ├── .env.example
│   └── requirements.txt
├── ml_models/                  # Root model artifacts
├── tests/                      # Pytest test suite
├── pyproject.toml              # Project configuration & dependencies
└── README.md
```

---

## ⚙️ Configuration

Sample YAML experiment config (`configs/experiment.yaml`):

```yaml
experiment:
  name: "vehicle_emission_prediction"
  model_type: "xgboost"
  random_state: 42

data:
  path: "data/raw/emissions.csv"
  target: "status"
  test_size: 0.2

training:
  cross_validation: 5
  hyperparameters:
    n_estimators: 200
    max_depth: 6
    learning_rate: 0.05
```

---

## 🗺️ Roadmap

- [x] Core ML training pipeline (scikit-learn)
- [x] XGBoost, LightGBM, CatBoost support
- [x] Automated feature engineering pipeline
- [x] FastAPI REST API with JWT authentication
- [x] SHAP & LIME explainability integration
- [x] Automated PDF report generation
- [x] Command-line interface (CLI)
- [ ] React web dashboard
- [ ] Model versioning & artifact registry (MLflow)
- [ ] Optuna hyperparameter optimization
- [ ] Docker & Docker Compose containerization
- [ ] Real-time prediction WebSocket streaming

---

## 🤝 Contributing

Contributions are welcome! Here's how to contribute:

1. **Fork** the repository
2. **Create** your feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'feat: add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) — Web framework
- [scikit-learn](https://scikit-learn.org/) — Machine learning library
- [XGBoost](https://xgboost.ai/) & [LightGBM](https://lightgbm.readthedocs.io/) — Gradient boosting
- [SHAP](https://shap.readthedocs.io/) & [LIME](https://github.com/marcotcr/lime) — Model interpretability
- [SQLAlchemy](https://www.sqlalchemy.org/) — Database ORM
- [ReportLab](https://www.reportlab.com/) — PDF generation engine

---

<div align="center">

**Built with ❤️ by [Shelum Hansana](https://github.com/ShelumHansana)**

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:7F00FF,100:E100FF&height=120&section=footer" width="100%" />

</div>
