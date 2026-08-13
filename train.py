"""
PredictV — Manual Training Script
==================================
Run this script to train all ML models on petrol motorbike data.

Usage:
    python train.py
"""

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
)

from predictv.training import Trainer

if __name__ == "__main__":
    print("=" * 60)
    print("  PredictV — Training All Models (Petrol Motorbikes)")
    print("=" * 60)
    print()

    trainer = Trainer()
    results = trainer.run()

    print()
    print(f"[OK] Training complete! {len(results)} model groups trained.")
    print("     Models saved to: ml_models/")
