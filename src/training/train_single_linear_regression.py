import pandas as pd
import numpy as np
import os
import logging
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def train_and_evaluate_single_model(train_dir, test_dir, model_dir):
    """
    Combines datasets from Plant 1 and Plant 2 to train a single, unified
    Linear Regression model. Evaluates it on both joint and plant-specific test sets.
    """
    os.makedirs(model_dir, exist_ok=True)
    
    # Base feature columns
    base_features = [
        'SOURCE_KEY_encoded', 'AMBIENT_TEMPERATURE_scaled', 'MODULE_TEMPERATURE_scaled', 
        'IRRADIATION_scaled', 'temp_diff_scaled', 'AC_POWER_lag_15m_scaled', 
        'AC_POWER_lag_30m_scaled', 'IRRADIATION_lag_15m_scaled', 'IRRADIATION_lag_30m_scaled', 
        'rolling_irrad_1h_scaled', 'rolling_temp_1h_scaled', 'hour_scaled', 
        'month_scaled', 'day_of_year_scaled', 'minute_scaled'
    ]
    
    target_col = 'AC_POWER'
    
    logging.info("Loading Plant 1 and Plant 2 datasets...")
    p1_train = pd.read_csv(os.path.join(train_dir, 'Plant_1_train.csv'))
    p2_train = pd.read_csv(os.path.join(train_dir, 'Plant_2_train.csv'))
    p1_test = pd.read_csv(os.path.join(test_dir, 'Plant_1_test.csv'))
    p2_test = pd.read_csv(os.path.join(test_dir, 'Plant_2_test.csv'))
    
    # Create a feature 'is_plant_2' (4136001 is Plant 2, 4135001 is Plant 1)
    # This allows a single model to understand the offset and difference in scale between the plants.
    for df in [p1_train, p2_train, p1_test, p2_test]:
        df['is_plant_2'] = (df['PLANT_ID'] == 4136001).astype(int)
        
    # Final feature list including the plant identifier
    feature_cols = base_features + ['is_plant_2']
    
    # Concatenate to form a single train and single test dataset
    logging.info("Combining datasets...")
    train_df = pd.concat([p1_train, p2_train], ignore_index=True)
    test_df = pd.concat([p1_test, p2_test], ignore_index=True)
    
    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    X_test = test_df[feature_cols]
    y_test = test_df[target_col]
    
    logging.info(f"Total training samples: {X_train.shape[0]}")
    logging.info(f"Total testing samples: {X_test.shape[0]}")
    
    # Initialize and train the single Linear Regression model
    logging.info("Training single Linear Regression model...")
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Predict and evaluate on combined train & test
    y_train_pred = np.clip(model.predict(X_train), 0, None)
    y_test_pred = np.clip(model.predict(X_test), 0, None)
    
    logging.info("--- Joint Model Evaluation ---")
    logging.info(f"Combined Train - MAE: {mean_absolute_error(y_train, y_train_pred):.4f} kW | RMSE: {np.sqrt(mean_squared_error(y_train, y_train_pred)):.4f} kW | R2: {r2_score(y_train, y_train_pred):.4f}")
    logging.info(f"Combined Test  - MAE: {mean_absolute_error(y_test, y_test_pred):.4f} kW | RMSE: {np.sqrt(mean_squared_error(y_test, y_test_pred)):.4f} kW | R2: {r2_score(y_test, y_test_pred):.4f}")
    
    # Evaluate individually on Plant 1 and Plant 2 test sets to ensure high local fidelity
    logging.info("--- Individual Plant Evaluation on Combined Model ---")
    
    # Plant 1
    X_p1_test = p1_test[feature_cols]
    y_p1_test = p1_test[target_col]
    y_p1_pred = np.clip(model.predict(X_p1_test), 0, None)
    logging.info(f"Plant 1 Test - MAE: {mean_absolute_error(y_p1_test, y_p1_pred):.4f} kW | RMSE: {np.sqrt(mean_squared_error(y_p1_test, y_p1_pred)):.4f} kW | R2: {r2_score(y_p1_test, y_p1_pred):.4f}")
    
    # Plant 2
    X_p2_test = p2_test[feature_cols]
    y_p2_test = p2_test[target_col]
    y_p2_pred = np.clip(model.predict(X_p2_test), 0, None)
    logging.info(f"Plant 2 Test - MAE: {mean_absolute_error(y_p2_test, y_p2_pred):.4f} kW | RMSE: {np.sqrt(mean_squared_error(y_p2_test, y_p2_pred)):.4f} kW | R2: {r2_score(y_p2_test, y_p2_pred):.4f}")
    
    # Save the single model
    model_save_path = os.path.join(model_dir, 'single_linear_regression.joblib')
    joblib.dump(model, model_save_path)
    logging.info(f"Saved combined single model to {model_save_path}")

if __name__ == '__main__':
    TRAIN_DIR = r'C:\Users\pk\Documents\pk_intern\Solar Power Generation Prediction\data\splited\train'
    TEST_DIR = r'C:\Users\pk\Documents\pk_intern\Solar Power Generation Prediction\data\splited\test'
    MODEL_DIR = r'C:\Users\pk\Documents\pk_intern\Solar Power Generation Prediction\model'
    
    train_and_evaluate_single_model(TRAIN_DIR, TEST_DIR, MODEL_DIR)
