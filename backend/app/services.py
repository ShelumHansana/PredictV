"""The loaded models, created once and shared by the routers."""

from app.engine import MixtureModel, SymptomModel

mixture_model = MixtureModel()
symptom_model = SymptomModel()
