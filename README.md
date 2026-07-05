# PredictV 🚀

**A Python Machine Learning toolkit for model training and evaluation.**

PredictV provides a clean, modular framework for building, training, and evaluating ML models with minimal boilerplate.

## Features

- 📊 **Data Processing** — Load, clean, and transform datasets with built-in pipelines
- 🏋️ **Model Training** — Train models with configurable hyperparameters and cross-validation
- 📈 **Evaluation** — Comprehensive metrics, confusion matrices, and visual reports
- 💾 **Model Persistence** — Save and load trained models effortlessly
- ⚙️ **Configuration** — YAML-based experiment configs for reproducibility

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd PredictV

# Create a virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux

# Install in development mode
pip install -e ".[dev]"
```

### Usage

```python
from predictv.data.loader import DataLoader
from predictv.training.trainer import Trainer
from predictv.evaluation.evaluator import Evaluator

# Load data
loader = DataLoader()
X_train, X_test, y_train, y_test = loader.load_and_split("data/raw/dataset.csv", target="label")

# Train a model
trainer = Trainer(model_type="random_forest", random_state=42)
model = trainer.fit(X_train, y_train)

# Evaluate
evaluator = Evaluator(model)
report = evaluator.evaluate(X_test, y_test)
evaluator.plot_results(save_path="outputs/figures/")
print(report)
```

### CLI

```bash
# Train a model from config
predictv train --config configs/experiment.yaml

# Evaluate a saved model
predictv evaluate --model outputs/models/model.joblib --data data/raw/dataset.csv
```

## Project Structure

```
PredictV/
├── configs/              # YAML experiment configurations
├── data/
│   ├── raw/              # Raw datasets
│   └── processed/        # Processed/transformed data
├── outputs/
│   ├── models/           # Saved trained models
│   └── figures/          # Generated plots and reports
├── src/predictv/
│   ├── data/             # Data loading & preprocessing
│   ├── models/           # Model definitions & factories
│   ├── training/         # Training pipelines
│   ├── evaluation/       # Metrics & visualization
│   └── utils/            # Shared utilities
├── tests/                # Unit tests
├── pyproject.toml        # Project config & dependencies
└── README.md
```

## License

MIT
