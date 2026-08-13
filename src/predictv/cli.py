"""
PredictV CLI — Command-line interface for petrol motorbike model training and evaluation.

Usage:
    predictv train          Train all models (petrol motorbike data only)
    predictv train --data   Train with custom dataset path
"""

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
)


def main() -> None:
    """PredictV CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="predictv",
        description="PredictV — Petrol Motorbike Emission ML Training Toolkit",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ── train ────────────────────────────────────────────────
    train_parser = subparsers.add_parser("train", help="Train all ML models")
    train_parser.add_argument(
        "--data", type=str, default=None,
        help="Path to the dataset CSV (default: data/raw/dataset.csv)",
    )
    train_parser.add_argument(
        "--output", type=str, default=None,
        help="Directory to save trained models (default: ml_models/)",
    )

    # ── evaluate ─────────────────────────────────────────────
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate trained models")
    eval_parser.add_argument(
        "--results", type=str, default=None,
        help="Path to training_results.json",
    )

    args = parser.parse_args()

    if args.command == "train":
        from predictv.training import Trainer

        data_path = Path(args.data) if args.data else None
        model_dir = Path(args.output) if args.output else None
        trainer = Trainer(data_path=data_path, model_dir=model_dir)
        results = trainer.run()
        print(f"\n[OK] Training complete! {len(results)} model groups trained.")

    elif args.command == "evaluate":
        import json

        results_path = Path(args.results) if args.results else Path("ml_models/training_results.json")
        if not results_path.exists():
            print(f"[ERROR] Results file not found: {results_path}")
            sys.exit(1)

        with open(results_path) as f:
            results = json.load(f)

        print("\nTraining Results Summary")
        print("=" * 50)
        for model_group, metrics in results.items():
            print(f"\n  * {model_group}")
            if isinstance(metrics, dict):
                for name, vals in metrics.items():
                    if isinstance(vals, dict):
                        summary = ", ".join(f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}" for k, v in vals.items())
                        print(f"   {name}: {summary}")
                    else:
                        print(f"   {name}: {vals}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
