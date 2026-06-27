import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
warnings.filterwarnings('ignore')

# Set aesthetic theme for plots
sns.set_theme(style="whitegrid", palette="muted")

def main():
    # Define paths
    data_dir = r"C:\Users\pk\Documents\pk_intern\Solar Power Generation Prediction\data\raw"
    base_out_dir = r"C:\Users\pk\Documents\pk_intern\Solar Power Generation Prediction\src\preprocessing\Data_understanding"
    plots_dir = os.path.join(base_out_dir, "plots")

    os.makedirs(plots_dir, exist_ok=True)

    print("Loading datasets...")
    # Load data
    try:
        p1_gen = pd.read_csv(os.path.join(data_dir, "Plant_1_Generation_Data.csv"))
        p1_wea = pd.read_csv(os.path.join(data_dir, "Plant_1_Weather_Sensor_Data.csv"))
        p2_gen = pd.read_csv(os.path.join(data_dir, "Plant_2_Generation_Data.csv"))
        p2_wea = pd.read_csv(os.path.join(data_dir, "Plant_2_Weather_Sensor_Data.csv"))
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    datasets = {
        "Plant 1 Generation": p1_gen,
        "Plant 1 Weather": p1_wea,
        "Plant 2 Generation": p2_gen,
        "Plant 2 Weather": p2_wea
    }

    # Data Understanding Summary
    summary_file = os.path.join(base_out_dir, "data_summary.txt")
    print("Generating data summary...")
    with open(summary_file, "w") as f:
        for name, df in datasets.items():
            f.write(f"--- {name} ---\n")
            f.write(f"Shape (Rows, Columns): {df.shape}\n\n")
            
            f.write("Missing Values:\n")
            f.write(df.isnull().sum().to_string() + "\n\n")
            
            f.write("Statistical Description:\n")
            f.write(df.describe().to_string() + "\n\n")
            f.write("="*50 + "\n\n")
            
    print(f"Data summary saved to {summary_file}")

    # Convert DATE_TIME to datetime object
    print("Processing datetime columns...")
    for df in datasets.values():
        if 'DATE_TIME' in df.columns:
            df['DATE_TIME'] = pd.to_datetime(df['DATE_TIME'], format='mixed')

    # Merge Generation and Weather Data for Plant 1 for Visualization
    p1_merged = pd.merge(p1_gen, p1_wea, on=['DATE_TIME', 'PLANT_ID'], how='inner')

    # Feature Engineering for easy understanding
    p1_merged['Hour'] = p1_merged['DATE_TIME'].dt.hour
    p1_merged['Date'] = p1_merged['DATE_TIME'].dt.date

    # Exploratory Data Analysis (EDA) Plots
    print("Generating easily understandable EDA plots...")

    # 1. Average Power Generation by Hour of Day (The "Solar Curve")
    plt.figure(figsize=(12, 6))
    hourly_power = p1_merged.groupby('Hour')['DC_POWER'].mean().reset_index()
    sns.lineplot(data=hourly_power, x='Hour', y='DC_POWER', marker='o', color='green', linewidth=2.5)
    plt.title('Average DC Power Generated per Hour (The Solar Curve)', fontsize=16)
    plt.xlabel('Hour of the Day (0 = Midnight, 12 = Noon)', fontsize=12)
    plt.ylabel('Average DC Power (kW)', fontsize=12)
    plt.xticks(range(0, 24))
    plt.fill_between(hourly_power['Hour'], hourly_power['DC_POWER'], color='green', alpha=0.1)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "1_hourly_power_generation.png"))
    plt.close()

    # 2. Average Irradiation by Hour of Day
    plt.figure(figsize=(12, 6))
    hourly_irr = p1_merged.groupby('Hour')['IRRADIATION'].mean().reset_index()
    sns.lineplot(data=hourly_irr, x='Hour', y='IRRADIATION', marker='s', color='orange', linewidth=2.5)
    plt.title('Average Sunlight (Irradiation) per Hour', fontsize=16)
    plt.xlabel('Hour of the Day (0 = Midnight, 12 = Noon)', fontsize=12)
    plt.ylabel('Average Sunlight Intensity', fontsize=12)
    plt.xticks(range(0, 24))
    plt.fill_between(hourly_irr['Hour'], hourly_irr['IRRADIATION'], color='orange', alpha=0.1)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "2_hourly_irradiation.png"))
    plt.close()

    # 3. Scatter Plot with Regression Line - Irradiation vs Power
    plt.figure(figsize=(10, 6))
    sample_data = p1_merged.sample(n=2000, random_state=42) # sampling to avoid messy plots
    sns.regplot(data=sample_data, x='IRRADIATION', y='DC_POWER', 
                scatter_kws={'alpha':0.4, 'color':'#3498db'}, line_kws={'color':'red', 'linewidth':2})
    plt.title('How Sunlight impacts Power Generation (Irradiation vs DC Power)', fontsize=16)
    plt.xlabel('Sunlight Intensity (Irradiation)', fontsize=12)
    plt.ylabel('Power Generated (DC Power)', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "3_sunlight_vs_power_regression.png"))
    plt.close()

    # 4. Temperature Comparison (Ambient vs Module)
    plt.figure(figsize=(12, 6))
    hourly_temp = p1_merged.groupby('Hour')[['AMBIENT_TEMPERATURE', 'MODULE_TEMPERATURE']].mean().reset_index()
    sns.lineplot(data=hourly_temp, x='Hour', y='AMBIENT_TEMPERATURE', label='Air Temp (Ambient)', color='blue', linewidth=2)
    sns.lineplot(data=hourly_temp, x='Hour', y='MODULE_TEMPERATURE', label='Panel Temp (Module)', color='red', linewidth=2)
    plt.title('Air Temp vs Solar Panel Temp throughout the Day', fontsize=16)
    plt.xlabel('Hour of the Day', fontsize=12)
    plt.ylabel('Temperature (°C)', fontsize=12)
    plt.xticks(range(0, 24))
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "4_temperature_comparison.png"))
    plt.close()

    # 5. Correlation Heatmap (Simplified)
    plt.figure(figsize=(8, 6))
    key_cols = ['DC_POWER', 'DAILY_YIELD', 'AMBIENT_TEMPERATURE', 'MODULE_TEMPERATURE', 'IRRADIATION']
    corr_matrix = p1_merged[key_cols].corr()
    sns.heatmap(corr_matrix, annot=True, cmap='RdYlGn', fmt=".2f", vmin=-1, vmax=1, center=0)
    plt.title('How features relate to each other (Correlation)', fontsize=16)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "5_key_features_correlation.png"))
    plt.close()

    print(f"Plots generated and saved to {plots_dir}")
    print("EDA Complete!")

if __name__ == "__main__":
    main()
