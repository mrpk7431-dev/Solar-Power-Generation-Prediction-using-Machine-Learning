import pandas as pd
import numpy as np
import os
import json
import logging
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def evaluate_model(model_path, test_dir, evaluate_dir):
    """
    Loads the trained unified model, predicts on Plant 1 and Plant 2 test datasets,
    saves predictions, metrics, and visualization plots.
    """
    os.makedirs(evaluate_dir, exist_ok=True)
    
    # Load model
    logging.info(f"Loading model from {model_path}...")
    if not os.path.exists(model_path):
        logging.error("Model file not found! Train the model first.")
        return
    model = joblib.load(model_path)
    
    # Load test sets
    p1_test_path = os.path.join(test_dir, 'Plant_1_test.csv')
    p2_test_path = os.path.join(test_dir, 'Plant_2_test.csv')
    
    logging.info("Loading test datasets...")
    p1_test = pd.read_csv(p1_test_path)
    p2_test = pd.read_csv(p2_test_path)
    
    # Convert DATE_TIME to datetime for plotting/time analysis
    p1_test['DATE_TIME'] = pd.to_datetime(p1_test['DATE_TIME'])
    p2_test['DATE_TIME'] = pd.to_datetime(p2_test['DATE_TIME'])
    
    # Add plant indicator
    p1_test['is_plant_2'] = 0
    p2_test['is_plant_2'] = 1
    
    # Define feature cols
    feature_cols = [
        'SOURCE_KEY_encoded', 'AMBIENT_TEMPERATURE_scaled', 'MODULE_TEMPERATURE_scaled', 
        'IRRADIATION_scaled', 'temp_diff_scaled', 'AC_POWER_lag_15m_scaled', 
        'AC_POWER_lag_30m_scaled', 'IRRADIATION_lag_15m_scaled', 'IRRADIATION_lag_30m_scaled', 
        'rolling_irrad_1h_scaled', 'rolling_temp_1h_scaled', 'hour_scaled', 
        'month_scaled', 'day_of_year_scaled', 'minute_scaled', 'is_plant_2'
    ]
    target_col = 'AC_POWER'
    
    # Prepare combined data
    combined_test = pd.concat([p1_test, p2_test], ignore_index=True)
    
    # Generate predictions
    logging.info("Generating predictions...")
    p1_test['predicted_AC_POWER'] = np.clip(model.predict(p1_test[feature_cols]), 0, None)
    p2_test['predicted_AC_POWER'] = np.clip(model.predict(p2_test[feature_cols]), 0, None)
    combined_test['predicted_AC_POWER'] = np.clip(model.predict(combined_test[feature_cols]), 0, None)
    
    # Save predictions
    p1_pred_path = os.path.join(evaluate_dir, 'Plant_1_predictions.csv')
    p2_pred_path = os.path.join(evaluate_dir, 'Plant_2_predictions.csv')
    p1_test.to_csv(p1_pred_path, index=False)
    p2_test.to_csv(p2_pred_path, index=False)
    logging.info(f"Saved prediction files to {evaluate_dir}")
    
    # Compute metrics
    metrics = {}
    for name, df in [('Plant_1', p1_test), ('Plant_2', p2_test), ('Combined', combined_test)]:
        y_true = df[target_col]
        y_pred = df['predicted_AC_POWER']
        
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        r2 = r2_score(y_true, y_pred)
        
        metrics[name] = {
            'MAE': round(float(mae), 4),
            'RMSE': round(float(rmse), 4),
            'R2_Score': round(float(r2), 4)
        }
        logging.info(f"{name} metrics - MAE: {mae:.4f} kW | RMSE: {rmse:.4f} kW | R2: {r2:.4f}")
        
    # Save metrics JSON
    metrics_path = os.path.join(evaluate_dir, 'metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=4)
    logging.info(f"Saved metrics to {metrics_path}")
    
    # --- Visualization Generating ---
    logging.info("Generating evaluation plots...")
    sns.set_theme(style='darkgrid')
    
    # 1. Scatter plots: Actual vs Predicted
    for name, df in [('Plant 1', p1_test), ('Plant 2', p2_test)]:
        plt.figure(figsize=(8, 6))
        sns.scatterplot(x='AC_POWER', y='predicted_AC_POWER', data=df, alpha=0.3, color='royalblue' if '1' in name else 'darkorange')
        
        # Identity line
        max_val = max(df['AC_POWER'].max(), df['predicted_AC_POWER'].max())
        plt.plot([0, max_val], [0, max_val], 'r--', lw=2, label='Perfect prediction')
        
        plt.title(f"{name} - Actual vs Predicted AC Power", fontsize=14)
        plt.xlabel("Actual AC Power (kW)", fontsize=12)
        plt.ylabel("Predicted AC Power (kW)", fontsize=12)
        plt.legend()
        plt.tight_layout()
        
        plot_path = os.path.join(evaluate_dir, f"{name.replace(' ', '_')}_actual_vs_predicted.png")
        plt.savefig(plot_path, dpi=150)
        plt.close()
        logging.info(f"Saved actual-vs-predicted plot for {name} to {plot_path}")
        
    # 2. Time-Series Comparison: Sub-selection (3 days for one specific inverter)
    # This keeps the plot clean and readable
    for name, df in [('Plant 1', p1_test), ('Plant 2', p2_test)]:
        # Select first inverter ID available
        inverter_id = df['SOURCE_KEY'].unique()[0]
        # Filter for that inverter
        inv_df = df[df['SOURCE_KEY'] == inverter_id].copy()
        
        # Sort and select first 3 days of dates
        inv_df = inv_df.sort_values(by='DATE_TIME')
        min_date = inv_df['DATE_TIME'].min()
        end_date = min_date + pd.Timedelta(days=3)
        plot_df = inv_df[(inv_df['DATE_TIME'] >= min_date) & (inv_df['DATE_TIME'] <= end_date)]
        
        plt.figure(figsize=(12, 5))
        plt.plot(plot_df['DATE_TIME'], plot_df['AC_POWER'], label='Actual Power', color='black', alpha=0.7, lw=2)
        plt.plot(plot_df['DATE_TIME'], plot_df['predicted_AC_POWER'], label='Predicted Power', color='crimson', linestyle='--', lw=2)
        
        plt.title(f"{name} (Inverter: {inverter_id}) - 3-Day Forecast Comparison", fontsize=14)
        plt.xlabel("Time", fontsize=12)
        plt.ylabel("AC Power (kW)", fontsize=12)
        plt.xticks(rotation=15)
        plt.legend()
        plt.tight_layout()
        
        ts_plot_path = os.path.join(evaluate_dir, f"{name.replace(' ', '_')}_time_series_comparison.png")
        plt.savefig(ts_plot_path, dpi=150)
        plt.close()
        logging.info(f"Saved time-series forecast plot for {name} to {ts_plot_path}")
        
    logging.info("Evaluation complete!")

if __name__ == '__main__':
    MODEL_PATH = r'C:\Users\pk\Documents\pk_intern\Solar Power Generation Prediction\model\single_linear_regression.joblib'
    TEST_DIR = r'C:\Users\pk\Documents\pk_intern\Solar Power Generation Prediction\data\splited\test'
    EVALUATE_DIR = r'C:\Users\pk\Documents\pk_intern\Solar Power Generation Prediction\src\training\evaluate'
    
    evaluate_model(MODEL_PATH, TEST_DIR, EVALUATE_DIR)
