"""Model evaluation script with comprehensive metrics and visualizations."""

import json
import os
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_curve, auc
)
from sklearn.preprocessing import label_binarize
from sklearn.model_selection import cross_val_score
import yaml

from preprocess import load_data, preprocess_data


def load_params():
    """Load parameters from params.yaml"""
    with open('params.yaml', 'r') as f:
        return yaml.safe_load(f)


def evaluate_model(model, X_test, y_test, class_names):
    """Comprehensive model evaluation"""
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)
    
    # Basic metrics
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, average='weighted'),
        'recall': recall_score(y_test, y_pred, average='weighted'),
        'f1_score': f1_score(y_test, y_pred, average='weighted')
    }
    
    # Per-class metrics
    report = classification_report(y_test, y_pred, target_names=class_names, output_dict=True)
    metrics['per_class'] = report
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    metrics['confusion_matrix'] = cm.tolist()
    
    return metrics, y_pred, y_pred_proba


def plot_confusion_matrix(cm, class_names, save_path):
    """Plot and save confusion matrix"""
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=class_names, yticklabels=class_names)
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_roc_curves(y_test, y_pred_proba, class_names, save_path):
    """Plot ROC curves for multiclass classification"""
    # Binarize the output
    y_test_bin = label_binarize(y_test, classes=[0, 1, 2])
    n_classes = y_test_bin.shape[1]
    
    plt.figure(figsize=(10, 8))
    
    # Plot ROC curve for each class
    for i in range(n_classes):
        fpr, tpr, _ = roc_curve(y_test_bin[:, i], y_pred_proba[:, i])
        roc_auc = auc(fpr, tpr)
        
        plt.plot(fpr, tpr, linewidth=2,
                label=f'{class_names[i]} (AUC = {roc_auc:.2f})')
    
    # Plot diagonal line
    plt.plot([0, 1], [0, 1], 'k--', linewidth=2)
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curves - Multiclass Classification')
    plt.legend(loc="lower right")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_prediction_distribution(y_test, y_pred, class_names, save_path):
    """Plot prediction distribution"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # True distribution
    unique, counts = np.unique(y_test, return_counts=True)
    ax1.bar([class_names[i] for i in unique], counts, color='skyblue', alpha=0.7)
    ax1.set_title('True Distribution')
    ax1.set_ylabel('Count')
    
    # Predicted distribution
    unique, counts = np.unique(y_pred, return_counts=True)
    ax2.bar([class_names[i] for i in unique], counts, color='lightcoral', alpha=0.7)
    ax2.set_title('Predicted Distribution')
    ax2.set_ylabel('Count')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_feature_importance(model, feature_names, save_path):
    """Plot feature importance if available"""
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1]
        
        plt.figure(figsize=(10, 6))
        plt.bar(range(len(importances)), importances[indices])
        plt.xticks(range(len(importances)), [feature_names[i] for i in indices], rotation=45)
        plt.title('Feature Importance')
        plt.ylabel('Importance')
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return importances.tolist()
    
    return None


def cross_validate_model(model, X, y, params):
    """Perform cross-validation"""
    cv_params = params['evaluate']['cross_validation']
    
    scores = cross_val_score(
        model, X, y, 
        cv=cv_params['cv_folds'], 
        scoring=cv_params['scoring']
    )
    
    return {
        'cv_scores': scores.tolist(),
        'cv_mean': scores.mean(),
        'cv_std': scores.std()
    }


def main():
    """Main evaluation function"""
    print("🔍 Starting model evaluation...")
    
    # Create directories
    os.makedirs('metrics', exist_ok=True)
    os.makedirs('plots', exist_ok=True)
    
    # Load parameters
    params = load_params()
    
    # Load data
    df = load_data('data/iris.csv')
    X_train, X_test, y_train, y_test = preprocess_data(df)
    
    # Load trained model
    model = joblib.load('artifacts/best_model.pkl')
    
    # Class names
    class_names = ['setosa', 'versicolor', 'virginica']
    feature_names = ['sepal_length', 'sepal_width', 'petal_length', 'petal_width']
    
    # Evaluate model
    metrics, y_pred, y_pred_proba = evaluate_model(model, X_test, y_test, class_names)
    
    # Cross-validation
    cv_results = cross_validate_model(model, X_train, y_train, params)
    metrics['cross_validation'] = cv_results
    
    # Feature importance
    feature_importance = plot_feature_importance(model, feature_names, 'plots/feature_importance.png')
    if feature_importance:
        metrics['feature_importance'] = dict(zip(feature_names, feature_importance))
    
    # Generate plots
    plot_confusion_matrix(
        np.array(metrics['confusion_matrix']), 
        class_names, 
        'plots/confusion_matrix.png'
    )
    
    plot_roc_curves(y_test, y_pred_proba, class_names, 'plots/roc_curves.png')
    
    plot_prediction_distribution(y_test, y_pred, class_names, 'plots/prediction_distribution.png')
    
    # Save metrics
    with open('metrics/evaluation.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Print summary
    print(f"✅ Model Evaluation Complete!")
    print(f"   Accuracy: {metrics['accuracy']:.4f}")
    print(f"   F1 Score: {metrics['f1_score']:.4f}")
    print(f"   CV Score: {cv_results['cv_mean']:.4f} ± {cv_results['cv_std']:.4f}")
    print(f"📊 Plots saved to 'plots/' directory")
    print(f"📈 Metrics saved to 'metrics/evaluation.json'")


if __name__ == "__main__":
    main()