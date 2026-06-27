import pandas as pd
import numpy as np
import os
import logging
# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
def engineer_features(processed_dir, features_dir):
    """
    Validates data by filtering out anomalies (e.g., inverter outages),
    and creates new features (temporal, differences, lags, and rolling stats).
    Saves the engineered datasets to the features directory.
    """
    os.makedirs(features_dir, exist_ok=True)
    
    p1_path = os.path.join(processed_dir, 'Plant_1_Cleaned_Merged.csv')
    p2_path = os.path.join(processed_dir, 'Plant_2_Cleaned_Merged.csv')
    
    logging.info("Loading processed datasets...")
    df1 = pd.read_csv(p1_path)
    df2 = pd.read_csv(p2_path)
    
    # Parse DATE_TIME back to datetime objects
    df1['DATE_TIME'] = pd.to_datetime(df1['DATE_TIME'])
    df2['DATE_TIME'] = pd.to_datetime(df2['DATE_TIME'])
    
    # Process both plants
    for plant_id, df in [('Plant_1', df1), ('Plant_2', df2)]:
        logging.info(f"Processing features for {plant_id}...")
        
        # 1. Validation & Data Cleaning (Filtering anomalies)
        # Inverter outages: High irradiation (> 0.1) but zero AC power
        outage_mask = (df['IRRADIATION'] > 0.1) & (df['AC_POWER'] == 0)
        logging.info(f"Removing {outage_mask.sum()} anomaly records (inverter outages) from {plant_id}")
        df_valid = df[~outage_mask].copy()
        
        # Cap any negative power or yield values to 0
        df_valid['DC_POWER'] = df_valid['DC_POWER'].clip(lower=0)
        df_valid['AC_POWER'] = df_valid['AC_POWER'].clip(lower=0)
        df_valid['DAILY_YIELD'] = df_valid['DAILY_YIELD'].clip(lower=0)
        
        # Sort by SOURCE_KEY and DATE_TIME for correct sequential shift/rolling operations
        df_valid = df_valid.sort_values(by=['SOURCE_KEY', 'DATE_TIME']).reset_index(drop=True)
        
        # 2. Time-based features
        df_valid['hour'] = df_valid['DATE_TIME'].dt.hour
        df_valid['month'] = df_valid['DATE_TIME'].dt.month
        df_valid['day_of_year'] = df_valid['DATE_TIME'].dt.dayofyear
        df_valid['minute'] = df_valid['DATE_TIME'].dt.minute
        
        # 3. Temperature differences
        # Module temperature should be higher than ambient; the difference is indicative of thermal heat loss/efficiency
        df_valid['temp_diff'] = df_valid['MODULE_TEMPERATURE'] - df_valid['AMBIENT_TEMPERATURE']
        
        # 4. Lag Features (grouped by inverter SOURCE_KEY to avoid cross-talk between inverters)
        # Shift key parameters by 1 period (15 mins) and 2 periods (30 mins)
        df_valid['AC_POWER_lag_15m'] = df_valid.groupby('SOURCE_KEY')['AC_POWER'].shift(1)
        df_valid['AC_POWER_lag_30m'] = df_valid.groupby('SOURCE_KEY')['AC_POWER'].shift(2)
        
        df_valid['IRRADIATION_lag_15m'] = df_valid.groupby('SOURCE_KEY')['IRRADIATION'].shift(1)
        df_valid['IRRADIATION_lag_30m'] = df_valid.groupby('SOURCE_KEY')['IRRADIATION'].shift(2)
        
        # 5. Rolling average features (last 1 hour = 4 periods)
        df_valid['rolling_irrad_1h'] = df_valid.groupby('SOURCE_KEY')['IRRADIATION'].transform(
            lambda x: x.rolling(4, min_periods=1).mean()
        )
        df_valid['rolling_temp_1h'] = df_valid.groupby('SOURCE_KEY')['AMBIENT_TEMPERATURE'].transform(
            lambda x: x.rolling(4, min_periods=1).mean()
        )
        
        # Drop rows with NaNs resulting from lag calculations (first 2 records of each inverter)
        before_drop_len = len(df_valid)
        df_valid = df_valid.dropna().reset_index(drop=True)
        after_drop_len = len(df_valid)
        logging.info(f"Dropped {before_drop_len - after_drop_len} boundary rows with NaN lag values for {plant_id}")
        
        # Save features to CSV
        out_path = os.path.join(features_dir, f"{plant_id}_Features.csv")
        df_valid.to_csv(out_path, index=False)
        logging.info(f"Saved engineered features for {plant_id} to {out_path} (Shape: {df_valid.shape})")
if __name__ == '__main__':
    PROCESSED_DIR = r'C:\Users\pk\Documents\pk_intern\Solar Power Generation Prediction\data\processed'
    FEATURES_DIR = r'C:\Users\pk\Documents\pk_intern\Solar Power Generation Prediction\data\features'
    engineer_features(PROCESSED_DIR, FEATURES_DIR)
