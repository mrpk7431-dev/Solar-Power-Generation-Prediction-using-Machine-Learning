import pandas as pd
import os
import logging
# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
def clean_and_merge_data(raw_dir, processed_dir):
    """
    Reads raw generation and weather data, cleans it by standardizing datetime,
    renaming columns, removing potential duplicates/nulls, and merging them.
    Saves the output to the processed directory.
    """
    # Ensure processed directory exists
    os.makedirs(processed_dir, exist_ok=True)
    
    # Define file paths
    p1_gen_path = os.path.join(raw_dir, 'Plant_1_Generation_Data.csv')
    p1_wea_path = os.path.join(raw_dir, 'Plant_1_Weather_Sensor_Data.csv')
    p2_gen_path = os.path.join(raw_dir, 'Plant_2_Generation_Data.csv')
    p2_wea_path = os.path.join(raw_dir, 'Plant_2_Weather_Sensor_Data.csv')
    
    logging.info("Loading raw datasets...")
    # Load data
    df1_gen = pd.read_csv(p1_gen_path)
    df1_wea = pd.read_csv(p1_wea_path)
    df2_gen = pd.read_csv(p2_gen_path)
    df2_wea = pd.read_csv(p2_wea_path)
    
    logging.info("Standardizing DATE_TIME formats...")
    # Convert DATE_TIME to datetime objects
    # Plant 1 Generation has format like 15-05-2020 00:00 (DD-MM-YYYY HH:MM)
    df1_gen['DATE_TIME'] = pd.to_datetime(df1_gen['DATE_TIME'], format='%d-%m-%Y %H:%M')
    # Others have format like 2020-05-15 00:00:00 (YYYY-MM-DD HH:MM:SS)
    df1_wea['DATE_TIME'] = pd.to_datetime(df1_wea['DATE_TIME'], format='%Y-%m-%d %H:%M:%S')
    df2_gen['DATE_TIME'] = pd.to_datetime(df2_gen['DATE_TIME'], format='%Y-%m-%d %H:%M:%S')
    df2_wea['DATE_TIME'] = pd.to_datetime(df2_wea['DATE_TIME'], format='%Y-%m-%d %H:%M:%S')
    
    # Rename SOURCE_KEY in weather data to avoid confusion when merging
    df1_wea = df1_wea.rename(columns={'SOURCE_KEY': 'WEATHER_SENSOR_KEY'})
    df2_wea = df2_wea.rename(columns={'SOURCE_KEY': 'WEATHER_SENSOR_KEY'})
    
    logging.info("Dropping duplicates and handling missing values...")
    # Drop duplicates
    df1_gen = df1_gen.drop_duplicates()
    df1_wea = df1_wea.drop_duplicates()
    df2_gen = df2_gen.drop_duplicates()
    df2_wea = df2_wea.drop_duplicates()
    
    # Drop nulls if any
    df1_gen = df1_gen.dropna()
    df1_wea = df1_wea.dropna()
    df2_gen = df2_gen.dropna()
    df2_wea = df2_wea.dropna()
    
    logging.info("Merging Generation and Weather data...")
    # Merge on DATE_TIME and PLANT_ID
    # Weather is recorded at plant level, generation is at inverter (SOURCE_KEY) level.
    # Therefore, we merge by DATE_TIME and PLANT_ID. Each inverter's record gets the plant's weather data for that time.
    df1_merged = pd.merge(df1_gen, df1_wea, on=['DATE_TIME', 'PLANT_ID'], how='inner')
    df2_merged = pd.merge(df2_gen, df2_wea, on=['DATE_TIME', 'PLANT_ID'], how='inner')
    
    # Sort by time and source key for neatness
    df1_merged = df1_merged.sort_values(by=['DATE_TIME', 'SOURCE_KEY']).reset_index(drop=True)
    df2_merged = df2_merged.sort_values(by=['DATE_TIME', 'SOURCE_KEY']).reset_index(drop=True)
    
    logging.info("Saving cleaned and merged data...")
    # Save to processed folder
    df1_out_path = os.path.join(processed_dir, 'Plant_1_Cleaned_Merged.csv')
    df2_out_path = os.path.join(processed_dir, 'Plant_2_Cleaned_Merged.csv')
    
    df1_merged.to_csv(df1_out_path, index=False)
    df2_merged.to_csv(df2_out_path, index=False)
    
    logging.info(f"Cleaned Plant 1 data saved to {df1_out_path} (Shape: {df1_merged.shape})")
    logging.info(f"Cleaned Plant 2 data saved to {df2_out_path} (Shape: {df2_merged.shape})")
if __name__ == '__main__':
    RAW_DIR = r'C:\Users\pk\Documents\pk_intern\Solar Power Generation Prediction\data\raw'
    PROCESSED_DIR = r'C:\Users\pk\Documents\pk_intern\Solar Power Generation Prediction\data\processed'
    clean_and_merge_data(RAW_DIR, PROCESSED_DIR)
