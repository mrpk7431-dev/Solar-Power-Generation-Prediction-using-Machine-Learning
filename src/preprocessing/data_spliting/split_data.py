import pandas as pd
import os
import logging
import shutil
# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
def split_and_organize_data(validation_dir, splited_dir):
    """
    Organizes the scaled train and validation datasets from validation_dir
    into separate train and test directories inside splited_dir.
    """
    train_dest_dir = os.path.join(splited_dir, 'train')
    test_dest_dir = os.path.join(splited_dir, 'test')
    
    os.makedirs(train_dest_dir, exist_ok=True)
    os.makedirs(test_dest_dir, exist_ok=True)
    
    # Mapping of source file in validation_dir to destination in splited_dir
    files_map = {
        'Plant_1_train_scaled.csv': ('train', 'Plant_1_train.csv'),
        'Plant_2_train_scaled.csv': ('train', 'Plant_2_train.csv'),
        'Plant_1_val_scaled.csv': ('test', 'Plant_1_test.csv'),
        'Plant_2_val_scaled.csv': ('test', 'Plant_2_test.csv')
    }
    
    logging.info("Splitting and organizing files...")
    for filename, (subdir, dest_name) in files_map.items():
        src_path = os.path.join(validation_dir, filename)
        dest_path = os.path.join(splited_dir, subdir, dest_name)
        
        if os.path.exists(src_path):
            logging.info(f"Copying and renaming {filename} -> {os.path.join(subdir, dest_name)}")
            shutil.copy2(src_path, dest_path)
            # Verify file contents are intact
            df = pd.read_csv(dest_path)
            logging.info(f"  Successfully organized {dest_name} in '{subdir}' folder. Shape: {df.shape}")
        else:
            logging.error(f"Source file {src_path} not found! Check scaling execution.")
if __name__ == '__main__':
    VALIDATION_DIR = r'C:\Users\pk\Documents\pk_intern\Solar Power Generation Prediction\data\validation'
    SPLITED_DIR = r'C:\Users\pk\Documents\pk_intern\Solar Power Generation Prediction\data\splited'
    split_and_organize_data(VALIDATION_DIR, SPLITED_DIR)
