from flask import Flask, render_template, request, jsonify
import os
import joblib
import numpy as np
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__, template_folder='templates', static_folder='static')

# File paths
MODEL_PATH = r'C:\Users\pk\Documents\pk_intern\Solar Power Generation Prediction\model\single_linear_regression.joblib'
SCALER_PATH = r'C:\Users\pk\Documents\pk_intern\Solar Power Generation Prediction\data\validation\scalers\Plant_1_scaler.joblib'

# Load the model
try:
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        logging.info("Model loaded successfully.")
    else:
        model = None
        logging.warning("Model file not found. Using fallback prediction.")
except Exception as e:
    model = None
    logging.error(f"Error loading model: {e}")

# Load the scaler
try:
    if os.path.exists(SCALER_PATH):
        scaler = joblib.load(SCALER_PATH)
        logging.info("Generic plant scaler loaded successfully.")
    else:
        scaler = None
        logging.warning("Scaler file not found. Using fallback prediction.")
except Exception as e:
    scaler = None
    logging.error(f"Error loading scaler: {e}")

def run_ml_prediction(irradiation, ambient_temp, hour):
    """
    Helper function to execute prediction using the loaded ML model.
    """
    if model is None or scaler is None:
        # Fallback simulation logic
        temp_loss = max(0, (ambient_temp + (irradiation * 25.0) - 25) * 0.004)
        if hour < 6 or hour > 19:
            return 0.0
        time_factor = np.sin((hour - 6) / 13.0 * np.pi)
        base_power = irradiation * 1400 * (1 - temp_loss) * time_factor
        val = max(0.0, base_power + np.random.normal(0, 4))
        return round(float(val), 2)
        
    # Standard flow using the trained machine learning model
    unscaled_features = np.copy(scaler.mean_)
    now = datetime.now()
    day_of_year = now.timetuple().tm_yday
    
    # Estimate Module Temp
    module_temp = ambient_temp + (irradiation * 25.0)
    
    # Overwrite features
    unscaled_features[0] = ambient_temp
    unscaled_features[1] = module_temp
    unscaled_features[2] = irradiation
    unscaled_features[3] = module_temp - ambient_temp
    unscaled_features[8] = irradiation
    unscaled_features[9] = ambient_temp
    unscaled_features[10] = hour
    unscaled_features[11] = now.month
    unscaled_features[12] = day_of_year
    unscaled_features[13] = 0
    
    # Scale and construct vector
    scaled_numerical = scaler.transform([unscaled_features])[0]
    
    feature_vector = [
        0,                     # SOURCE_KEY_encoded
        scaled_numerical[0],  # AMBIENT_TEMPERATURE_scaled
        scaled_numerical[1],  # MODULE_TEMPERATURE_scaled
        scaled_numerical[2],  # IRRADIATION_scaled
        scaled_numerical[3],  # temp_diff_scaled
        scaled_numerical[4],  # AC_POWER_lag_15m_scaled
        scaled_numerical[5],  # AC_POWER_lag_30m_scaled
        scaled_numerical[6],  # IRRADIATION_lag_15m_scaled
        scaled_numerical[7],  # IRRADIATION_lag_30m_scaled
        scaled_numerical[8],  # rolling_irrad_1h_scaled
        scaled_numerical[9],  # rolling_temp_1h_scaled
        scaled_numerical[10], # hour_scaled
        scaled_numerical[11], # month_scaled
        scaled_numerical[12], # day_of_year_scaled
        scaled_numerical[13], # minute_scaled
        0                      # is_plant_2
    ]
    
    pred = model.predict([feature_vector])[0]
    predicted_power = max(0.0, float(pred))
    
    if hour < 6 or hour > 19 or irradiation < 0.02:
        predicted_power = 0.0
        
    return round(predicted_power, 2)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Parse inputs
        irrad_start = float(data.get('irradiation_start', 0.0))
        irrad_end = float(data.get('irradiation_end', 0.8))
        
        temp_start = float(data.get('temperature_start', 20.0))
        temp_end = float(data.get('temperature_end', 30.0))
        
        hour_start = int(data.get('hour_start', 9))
        hour_end = int(data.get('hour_end', 17))
        
        # Validation checks
        hour_start = max(0, min(23, hour_start))
        hour_end = max(0, min(23, hour_end))
        
        # Ensure start hour is less than or equal to end hour
        if hour_start > hour_end:
            hour_start, hour_end = hour_end, hour_start
            
        hours_list = list(range(hour_start, hour_end + 1))
        num_steps = len(hours_list)
        
        hourly_data = []
        total_energy_kwh = 0.0
        
        # Loop through each hour and interpolate the weather parameters
        for idx, h in enumerate(hours_list):
            # Calculate interpolation fraction t
            t = idx / (num_steps - 1) if num_steps > 1 else 0.0
            
            # Linear interpolation of weather
            h_irrad = irrad_start + t * (irrad_end - irrad_start)
            h_temp = temp_start + t * (temp_end - temp_start)
            
            # Run prediction for this hour
            h_power = run_ml_prediction(h_irrad, h_temp, h)
            
            hourly_data.append({
                'hour': h,
                'power': h_power,
                'irradiation': round(h_irrad, 2),
                'temperature': round(h_temp, 1)
            })
            
            # Assuming power generated is constant for the hour (kW * 1 hour = kWh)
            total_energy_kwh += h_power
            
        power_start = hourly_data[0]['power']
        power_end = hourly_data[-1]['power']
        
        logging.info(f"Interval: {hour_start}:00 to {hour_end}:00 | Total Yield: {total_energy_kwh:.2f} kWh")
        
        return jsonify({
            'predicted_power_start': power_start,
            'predicted_power_end': power_end,
            'total_energy_kwh': round(total_energy_kwh, 2),
            'hourly_data': hourly_data
        })
        
    except Exception as e:
        logging.error(f"Error in range prediction endpoint: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
