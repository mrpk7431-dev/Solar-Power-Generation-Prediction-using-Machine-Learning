import pandas as pd
import numpy as np
import os
import logging
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib
# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
def scale_and_split_data(features_dir, validation_dir):
    """
    Splits the datasets into training (first 27 days) and validation (last 7 days) sets,
    scales numerical columns using standard scaling (fit on training only),
    and encodes categorical columns (SOURCE_KEY). Saves the output datasets and scalers.
    """
    # Create target directory and scalers subdirectory
    os.makedirs(validation_dir, exist_ok=True)
    scalers_dir = os.path.join(validation_dir, 'scalers')
    os.makedirs(scalers_dir, exist_ok=True)
    
    p1_path = os.path.join(features_dir, 'Plant_1_Features.csv')
    p2_path = os.path.join(features_dir, 'Plant_2_Features.csv')
    
    logging.info("Loading feature engineered datasets...")
    df1 = pd.read_csv(p1_path)
    df2 = pd.read_csv(p2_path)
    
    # Parse DATE_TIME to datetime
    df1['DATE_TIME'] = pd.to_datetime(df1['DATE_TIME'])
    df2['DATE_TIME'] = pd.to_datetime(df2['DATE_TIME'])
    
    # Define columns to scale
    numerical_cols = [
        'AMBIENT_TEMPERATURE', 'MODULE_TEMPERATURE', 'IRRADIATION', 'temp_diff',
        'AC_POWER_lag_15m', 'AC_POWER_lag_30m', 'IRRADIATION_lag_15m', 'IRRADIATION_lag_30m',
        'rolling_irrad_1h', 'rolling_temp_1h', 'hour', 'month', 'day_of_year', 'minute'
    ]
    
    # Define columns to keep unchanged (e.g. target, timestamp, plant_id)
    keep_cols = ['DATE_TIME', 'PLANT_ID', 'SOURCE_KEY', 'AC_POWER', 'DC_POWER', 'DAILY_YIELD', 'TOTAL_YIELD']
    
    # Time-based split: Use June 11, 2020 as the split point (provides roughly 80/20 train/val split)
    split_date = pd.to_datetime('2020-06-11 00:00:00')
    
    for plant_name, df in [('Plant_1', df1), ('Plant_2', df2)]:
        logging.info(f"Processing scaling and splitting for {plant_name}...")
        
        # Split into training and validation sets
        train_df = df[df['DATE_TIME'] < split_date].copy()
        val_df = df[df['DATE_TIME'] >= split_date].copy()
        
        logging.info(f"{plant_name} - Train samples: {len(train_df)} ({train_df['DATE_TIME'].min()} to {train_df['DATE_TIME'].max()})")
        logging.info(f"{plant_name} - Validation samples: {len(val_df)} ({val_df['DATE_TIME'].min()} to {val_df['DATE_TIME'].max()})")
        
        # 1. Fit LabelEncoder for SOURCE_KEY on training set, then transform both
        le = LabelEncoder()
        train_df['SOURCE_KEY_encoded'] = le.fit_transform(train_df['SOURCE_KEY'])
        # Handle unseen labels in validation if any, though it should be identical inverters
        val_df['SOURCE_KEY_encoded'] = val_df['SOURCE_KEY'].map(lambda s: le.transform([s])[0] if s in le.classes_ else -1)
        
        # 2. Fit StandardScaler on numerical columns of training set, then transform both
        scaler = StandardScaler()
        
        # Scale training numerical columns
        train_scaled_num = scaler.fit_transform(train_df[numerical_cols])
        val_scaled_num = scaler.transform(val_df[numerical_cols])
        
        # Convert scaled values to dataframe
        train_scaled_num_df = pd.DataFrame(train_scaled_num, columns=[f"{col}_scaled" for col in numerical_cols], index=train_df.index)
        val_scaled_num_df = pd.DataFrame(val_scaled_num, columns=[f"{col}_scaled" for col in numerical_cols], index=val_df.index)
        
        # Combine scaled numerical features, encoded categories, and keep columns
        final_train_df = pd.concat([train_df[keep_cols + ['SOURCE_KEY_encoded']], train_scaled_num_df], axis=1)
        final_val_df = pd.concat([val_df[keep_cols + ['SOURCE_KEY_encoded']], val_scaled_num_df], axis=1)
        
        # 3. Save scaled datasets
        train_out_path = os.path.join(validation_dir, f"{plant_name}_train_scaled.csv")
        val_out_path = os.path.join(validation_dir, f"{plant_name}_val_scaled.csv")
        
        final_train_df.to_csv(train_out_path, index=False)
        final_val_df.to_csv(val_out_path, index=False)
        
        # 4. Save scaler and label encoder objects
        scaler_save_path = os.path.join(scalers_dir, f"{plant_name}_scaler.joblib")
        encoder_save_path = os.path.join(scalers_dir, f"{plant_name}_encoder.joblib")
        joblib.dump(scaler, scaler_save_path)
        joblib.dump(le, encoder_save_path)
        
        logging.info(f"Saved scaled datasets for {plant_name}:")
        logging.info(f"  - Train: {train_out_path}")
        logging.info(f"  - Validation: {val_out_path}")
        logging.info(f"Saved preprocessing artifacts to {scalers_dir}")
if __name__ == '__main__':
    FEATURES_DIR = r'C:\Users\pk\Documents\pk_intern\Solar Power Generation Prediction\data\features'
    VALIDATION_DIR = r'C:\Users\pk\Documents\pk_intern\Solar Power Generation Prediction\data\validation'
    scale_and_split_data(FEATURES_DIR, VALIDATION_DIR)
