"""
Comprehensive model evaluation utilities for the Iris classification project.
This module provides functions for evaluating model performance, generating
detailed reports, and comparing multiple models.
"""

import os
from typing import Any, Dict, List, Tuple

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import cross_val_score, learning_curve


class ModelEvaluator:
    """Comprehensive model evaluation and comparison utilities"""

    def __init__(self, class_names: List[str] = None):
        self.class_names = class_names or ["setosa", "versicolor", "virginica"]

    def evaluate_single_model(
        self, model, X_test, y_test, X_train=None, y_train=None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive evaluation of a single model.
        Returns detailed metrics and evaluation results.
        """
        y_pred = model.predict(X_test)
        y_pred_proba = (
            model.predict_proba(X_test) if hasattr(model, "predict_proba") else None
        )

        # Basic classification metrics
        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision_macro": precision_score(y_test, y_pred, average="macro"),
            "precision_weighted": precision_score(y_test, y_pred, average="weighted"),
            "recall_macro": recall_score(y_test, y_pred, average="macro"),
            "recall_weighted": recall_score(y_test, y_pred, average="weighted"),
            "f1_macro": f1_score(y_test, y_pred, average="macro"),
            "f1_weighted": f1_score(y_test, y_pred, average="weighted"),
        }

        # Cross-validation scores if training data is provided
        if X_train is not None and y_train is not None:
            cv_scores = cross_val_score(
                model, X_train, y_train, cv=5, scoring="accuracy"
            )
            metrics.update(
                {
                    "cv_accuracy_mean": cv_scores.mean(),
                    "cv_accuracy_std": cv_scores.std(),
                    "cv_scores": cv_scores.tolist(),
                }
            )

        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        metrics["confusion_matrix"] = cm.tolist()

        # Per-class metrics
        class_report = classification_report(
            y_test, y_pred, output_dict=True, target_names=self.class_names
        )
        metrics["per_class_metrics"] = class_report

        # ROC AUC for multiclass (if probabilities available)
        if y_pred_proba is not None:
            try:
                # One-vs-rest ROC AUC
                auc_scores = roc_auc_score(
                    y_test, y_pred_proba, multi_class="ovr", average=None
                )
                metrics["roc_auc_per_class"] = auc_scores.tolist()
                metrics["roc_auc_macro"] = roc_auc_score(
                    y_test, y_pred_proba, multi_class="ovr", average="macro"
                )
            except Exception as e:
                print(f"Could not calculate ROC AUC: {e}")

        return metrics

    def compare_models(
        self, models_dict: Dict[str, Any], X_test, y_test, X_train=None, y_train=None
    ) -> Dict[str, Any]:
        """
        Compare multiple models and return comprehensive comparison results.
        models_dict should be {'model_name': model_object}
        """
        comparison_results = {}

        for model_name, model in models_dict.items():
            print(f"Evaluating {model_name}...")
            comparison_results[model_name] = self.evaluate_single_model(
                model, X_test, y_test, X_train, y_train
            )

        # Create summary comparison
        summary_metrics = [
            "accuracy",
            "f1_weighted",
            "precision_weighted",
            "recall_weighted",
        ]
        if X_train is not None:
            summary_metrics.append("cv_accuracy_mean")

        summary = {}
        for metric in summary_metrics:
            summary[metric] = {
                name: results[metric]
                for name, results in comparison_results.items()
                if metric in results
            }

        # Find best model for each metric
        best_models = {}
        for metric, scores in summary.items():
            if scores:
                best_model = max(scores.items(), key=lambda x: x[1])
                best_models[metric] = {"model": best_model[0], "score": best_model[1]}

        return {
            "detailed_results": comparison_results,
            "summary": summary,
            "best_models": best_models,
        }

    def generate_model_report(
        self, model_name: str, evaluation_results: Dict[str, Any]
    ) -> str:
        """Generate a formatted text report for a model's evaluation results"""
        report = f"\n{'='*50}\n"
        report += f"MODEL EVALUATION REPORT: {model_name.upper()}\n"
        report += f"{'='*50}\n\n"

        # Basic metrics
        report += "CLASSIFICATION METRICS:\n"
        report += f"  Accuracy:           {evaluation_results['accuracy']:.4f}\n"
        report += f"  Precision (macro):  {evaluation_results['precision_macro']:.4f}\n"
        report += f"  Recall (macro):     {evaluation_results['recall_macro']:.4f}\n"
        report += f"  F1-Score (macro):   {evaluation_results['f1_macro']:.4f}\n"
        report += f"  F1-Score (weighted): {evaluation_results['f1_weighted']:.4f}\n"

        # Cross-validation results
        if "cv_accuracy_mean" in evaluation_results:
            report += f"\nCROSS-VALIDATION RESULTS:\n"
            report += f"  CV Accuracy: {evaluation_results['cv_accuracy_mean']:.4f} ± {evaluation_results['cv_accuracy_std']:.4f}\n"

        # ROC AUC if available
        if "roc_auc_macro" in evaluation_results:
            report += f"\nROC AUC SCORES:\n"
            report += f"  Macro Average: {evaluation_results['roc_auc_macro']:.4f}\n"
            for i, class_name in enumerate(self.class_names):
                if i < len(evaluation_results["roc_auc_per_class"]):
                    report += f"  {class_name}: {evaluation_results['roc_auc_per_class'][i]:.4f}\n"

        # Per-class performance
        report += f"\nPER-CLASS PERFORMANCE:\n"
        per_class = evaluation_results["per_class_metrics"]
        for class_name in self.class_names:
            if class_name in per_class:
                metrics = per_class[class_name]
                report += f"  {class_name}:\n"
                report += f"    Precision: {metrics['precision']:.4f}\n"
                report += f"    Recall:    {metrics['recall']:.4f}\n"
                report += f"    F1-Score:  {metrics['f1-score']:.4f}\n"

        return report

    def save_evaluation_results(
        self, results: Dict[str, Any], output_dir: str = "artifacts"
    ):
        """Save evaluation results to files for later analysis"""
        os.makedirs(output_dir, exist_ok=True)

        # Save detailed results as joblib
        joblib.dump(results, os.path.join(output_dir, "evaluation_results.pkl"))

        # Save summary as CSV if it's a comparison
        if "summary" in results:
            summary_df = pd.DataFrame(results["summary"])
            summary_df.to_csv(os.path.join(output_dir, "model_comparison_summary.csv"))

        print(f"✅ Evaluation results saved to {output_dir}/")

    def plot_confusion_matrix(
        self, confusion_matrix, model_name: str, save_path: str = None
    ):
        """Create and optionally save a confusion matrix plot"""
        plt.figure(figsize=(8, 6))
        sns.heatmap(
            confusion_matrix,
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=self.class_names,
            yticklabels=self.class_names,
        )
        plt.title(f"Confusion Matrix - {model_name}")
        plt.xlabel("Predicted Label")
        plt.ylabel("True Label")

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"Confusion matrix saved to {save_path}")

        plt.show()


def evaluate_iris_models(
    models_dict: Dict[str, Any], X_train, X_test, y_train, y_test
) -> Dict[str, Any]:
    """
    Convenience function to evaluate Iris classification models.
    Returns comprehensive evaluation results for all provided models.
    """
    evaluator = ModelEvaluator()
    results = evaluator.compare_models(models_dict, X_test, y_test, X_train, y_train)

    # Print summary reports
    print("\n" + "=" * 60)
    print("MODEL COMPARISON SUMMARY")
    print("=" * 60)

    for model_name, model_results in results["detailed_results"].items():
        print(evaluator.generate_model_report(model_name, model_results))

    # Print best models summary
    print("\n" + "=" * 60)
    print("BEST MODELS BY METRIC")
    print("=" * 60)
    for metric, best_info in results["best_models"].items():
        print(f"{metric.upper()}: {best_info['model']} ({best_info['score']:.4f})")

    return results
