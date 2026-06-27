import pandas as pd
import numpy as np
import os
import json
import logging
import matplotlib.pyplot as plt
import seaborn as sns

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_accuracy_and_plot(evaluate_dir):
    """
    Loads saved test predictions, calculates capacity-normalized and volume-based
    accuracy percentages, saves them to JSON, and plots an accuracy comparison graph.
    """
    p1_path = os.path.join(evaluate_dir, 'Plant_1_predictions.csv')
    p2_path = os.path.join(evaluate_dir, 'Plant_2_predictions.csv')
    
    if not os.path.exists(p1_path) or not os.path.exists(p2_path):
        logging.error("Predictions files not found in evaluate folder! Run evaluation first.")
        return
        
    logging.info("Loading predictions...")
    p1_df = pd.read_csv(p1_path)
    p2_df = pd.read_csv(p2_path)
    
    # Calculate accuracy metrics
    results = {}
    
    for name, df in [('Plant_1', p1_df), ('Plant_2', p2_df)]:
        y_true = df['AC_POWER'].values
        y_pred = df['predicted_AC_POWER'].values
        
        # Absolute Errors
        abs_errors = np.abs(y_true - y_pred)
        mae = np.mean(abs_errors)
        
        # 1. Capacity-Normalized MAE Accuracy
        max_capacity = y_true.max()
        nmae = mae / max_capacity
        capacity_accuracy = (1 - nmae) * 100
        
        # 2. WAPE-Based (Volume-Based) Accuracy
        wape = np.sum(abs_errors) / np.sum(y_true)
        volume_accuracy = (1 - wape) * 100
        
        results[name] = {
            'MAE': round(float(mae), 4),
            'Max_Capacity_kW': round(float(max_capacity), 4),
            'Capacity_Accuracy_Percent': round(float(capacity_accuracy), 2),
            'Volume_Accuracy_Percent': round(float(volume_accuracy), 2)
        }
        
    # Calculate Combined metrics
    combined_true = np.concatenate([p1_df['AC_POWER'].values, p2_df['AC_POWER'].values])
    combined_pred = np.concatenate([p1_df['predicted_AC_POWER'].values, p2_df['predicted_AC_POWER'].values])
    combined_abs_errors = np.abs(combined_true - combined_pred)
    combined_mae = np.mean(combined_abs_errors)
    combined_max_capacity = combined_true.max()
    combined_capacity_accuracy = (1 - combined_mae / combined_max_capacity) * 100
    combined_volume_accuracy = (1 - np.sum(combined_abs_errors) / np.sum(combined_true)) * 100
    
    results['Combined'] = {
        'MAE': round(float(combined_mae), 4),
        'Max_Capacity_kW': round(float(combined_max_capacity), 4),
        'Capacity_Accuracy_Percent': round(float(combined_capacity_accuracy), 2),
        'Volume_Accuracy_Percent': round(float(combined_volume_accuracy), 2)
    }
    
    # Save accuracy data
    out_json_path = os.path.join(evaluate_dir, 'accuracy_results.json')
    with open(out_json_path, 'w') as f:
        json.dump(results, f, indent=4)
    logging.info(f"Saved accuracy data to {out_json_path}")
    
    # Print results
    for key, metrics in results.items():
        print(f"\n=== {key} Accuracy Metrics ===")
        print(f"  Capacity-Normalized Accuracy : {metrics['Capacity_Accuracy_Percent']}%")
        print(f"  Volume-Based Yield Accuracy  : {metrics['Volume_Accuracy_Percent']}%")
        print(f"  Mean Absolute Error (MAE)   : {metrics['MAE']} kW")
        print(f"  Maximum Observed Capacity    : {metrics['Max_Capacity_kW']} kW")
        
    # --- Generate Accuracy Graph ---
    sns.set_theme(style='whitegrid')
    
    # Prepare data for plotting
    plot_data = []
    for key in ['Plant_1', 'Plant_2', 'Combined']:
        plot_data.append({
            'Category': key.replace('_', ' '),
            'Accuracy': results[key]['Capacity_Accuracy_Percent'],
            'Metric Type': 'Capacity-Normalized Accuracy'
        })
        plot_data.append({
            'Category': key.replace('_', ' '),
            'Accuracy': results[key]['Volume_Accuracy_Percent'],
            'Metric Type': 'Volume-Based Yield Accuracy'
        })
    plot_df = pd.DataFrame(plot_data)
    
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(
        x='Category', 
        y='Accuracy', 
        hue='Metric Type', 
        data=plot_df, 
        palette='viridis'
    )
    
    # Add values on top of the bars
    for p in ax.patches:
        height = p.get_height()
        if height > 0:
            ax.annotate(f'{height:.2f}%',
                        (p.get_x() + p.get_width() / 2., height),
                        ha='center', va='bottom',
                        fontsize=11, color='black',
                        xytext=(0, 3),
                        textcoords='offset points')
            
    plt.title("Solar Power Prediction Model Accuracy Comparison", fontsize=14, fontweight='bold', pad=15)
    plt.ylabel("Accuracy Percentage (%)", fontsize=12)
    plt.xlabel("Dataset", fontsize=12)
    plt.ylim(0, 110)
    plt.legend(loc='lower right', frameon=True)
    plt.tight_layout()
    
    graph_path = os.path.join(evaluate_dir, 'accuracy_comparison_graph.png')
    plt.savefig(graph_path, dpi=150)
    plt.close()
    logging.info(f"Saved accuracy graph to {graph_path}")

if __name__ == '__main__':
    EVALUATE_DIR = r'C:\Users\pk\Documents\pk_intern\Solar Power Generation Prediction\src\training\evaluate'
    calculate_accuracy_and_plot(EVALUATE_DIR)
