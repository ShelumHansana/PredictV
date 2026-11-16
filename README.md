# PredictV — Petrol Motorbike Fault Finder

Answer a few simple questions about a petrol motorbike and get the most likely
faults, why the system thinks so, and how to fix each one. English and Sinhala,
light and dark theme.

| Layer | Stack |
|---|---|
| Frontend | React 18, TypeScript, Vite, React Router, three.js (3D bike) |
| Backend | FastAPI, SQLAlchemy |
| Database | SQLite (file `backend/data/predictv.db`; any SQLAlchemy URL via `DATABASE_URL`) |
| ML | scikit-learn RandomForest trained on EngineFaultDB |

## Run it

You need **Node.js 18+** and **Python 3.10+** installed. Then, in this folder:

```bash
npm run dev
```

The first run sets everything up by itself (Python environment in `.venv`,
Python packages, frontend packages, and retrains the model if your
scikit-learn version differs from the saved one). After that it starts in a few
seconds. Open the address it prints (normally http://localhost:5173).

| Command | What it does |
|---|---|
| `npm run dev` | API + React app with live reload |
| `npm test` | 20 backend tests + frontend type check |
| `npm run build` | Build the React app into `frontend/dist` |
| `npm start` | Build, then serve API and app from one port (production style) |
| `npm run train` | Retrain the exhaust-gas model |
| `npm run train:symptoms` | Train the learned symptom model from saved mechanic feedback |

Docker: `docker build -t predictv . && docker run -p 8000:8000 predictv`.

## Project structure

```
package.json            npm scripts (all handled by scripts/run.mjs)
scripts/run.mjs         setup + runner, no dependencies
backend/
  app/main.py           FastAPI app; also serves frontend/dist in production
  app/routers/          meta.py, diagnoses.py
  app/engine.py         diagnosis engine (rules + ML models)
  app/knowledge.py      faults, symptoms, fixes (EN + SI), emission limits
  app/features.py       answers -> numeric row for the learned model
  app/db.py             tables: diagnoses, feedback
  app/schemas.py  deps.py  config.py  services.py
  ml/train.py           trains models/mixture_*.joblib + metrics.json
  ml/train_symptoms.py  trains models/symptom_model.joblib from feedback
  data/raw/             EngineFaultDB_Final.csv (see data/SOURCE.md)
  tests/
frontend/src/
  pages/                HomePage, CheckPage, ResultPage, HistoryPage, AboutPage, NotFoundPage
  components/layout/    AppShell, Header
  components/ui/        Button, Panel, Badge, Field, Stepper, Notice
  components/check/     BikeStep, ServiceQuestion, SymptomStep, EmissionStep
  components/result/    Verdict, FaultCard, EmissionCard, ServiceStatus, FeedbackForm
  components/scene/     BikeFigure, BikeCanvas, buildBike (3D bike from shapes)
  api/  state/  hooks/  i18n/  styles/tokens.css
```

## How a result is produced

1. **Rules** (`knowledge.py`, `engine.py`): each of 11 faults lists the symptoms,
   overdue services and readings that point to it, with weights. This part is a
   rule-based expert system, **not machine learning**.
2. **Emission limits**: CO and HC against the Sri Lankan in-use limits for petrol
   motorcycles (CO ≤ 4 %, HC ≤ 6,000 ppm, as published at https://ecosri.lk/?p=5723).
3. **Mixture model (ML)**: RandomForest on EngineFaultDB reads the gas values →
   normal / rich / lean-or-ignition. It is refused outside its training range and
   never raises a fault by itself.
4. **Learned symptom model (ML, starts empty)**: riders can record what the
   mechanic actually found. `npm run train:symptoms` trains a classifier on those
   confirmed cases once there are at least 150, and the API then uses it to
   re-rank results. Until then it does not exist; nothing is generated to fill it.

## Model results

Numbers are written to `backend/models/metrics.json` by `ml/train.py` and shown
on the "How it works" page. With scikit-learn 1.9.1:

| Model | Inputs | Random 80/20 hold-out | Blocked 5-fold CV |
|---|---|---|---|
| full | CO, HC, CO₂, O₂, Lambda | 99.9 % | 98.1 % ± 3.5 |
| basic | CO, HC | 93.0 % | 90.8 % ± 2.8 |

Quote the blocked figure: rows are consecutive readings, so a random split puts
near-identical rows in both train and test. Numbers shift slightly between
scikit-learn versions.

## Limitations

1. **The exhaust-gas model is trained on a 1.4 L car engine, not a motorbike.**
   No public, labelled motorbike emission/fault dataset was found. Its classes
   do not line up reliably with real bike readings, which is why it only counts
   when the rider's own answers support the same fault.
2. "Lean mixture" and "low voltage" are merged: with the four original classes
   accuracy is 74 % and the model is at 50 % between those two.
3. The rule weights are workshop troubleshooting practice, not validated against
   a set of diagnosed bikes. "Likely / possible" is match strength, not probability.
4. No accounts. History is tied to an anonymous http-only cookie, so it is per
   browser and is lost if cookies are cleared. There is no rate limiting.
5. The Sinhala text has not been reviewed by a second reader.

## Data

`backend/data/raw/EngineFaultDB_Final.csv` — 55,999 laboratory readings from a
C14NE 1.4 L petrol engine (IEEE Access 2023, GPL-3.0). Links and details in
`backend/data/SOURCE.md`. No synthetic data is used.
