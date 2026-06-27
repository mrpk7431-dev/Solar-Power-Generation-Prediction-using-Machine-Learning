# ☀️ Solar Power Generation Prediction

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-Framework-green.svg)
![Machine Learning](https://img.shields.io/badge/Machine%20Learning-Scikit--Learn-orange.svg)
![Deployed on Render](https://img.shields.io/badge/Deployed-Render-purple.svg)

## 📌 Overview
This project is an end-to-end Machine Learning web application that predicts the power generation of a solar power plant based on weather parameters like ambient temperature and solar irradiation. 

The application is built using **Python, Scikit-Learn (Linear Regression), and Flask**, and is fully deployed on the web.

🌍 **Live Demo:** [Solar Power Generation Prediction](https://solar-power-generation-prediction-using.onrender.com)

## ✨ Features
- 🌤 **Weather-based Prediction:** Predicts power yield based on solar irradiation and temperature.
- 🕒 **Hourly Forecast:** Estimates the power generation over a specific time range.
- 📊 **Interactive Web UI:** Simple and clean user interface for providing inputs.
- 🚀 **Production-Ready:** Configured with `gunicorn` and fully deployed on Render.

## 🛠️ Tech Stack
- **Machine Learning:** `scikit-learn`, `pandas`, `numpy`, `joblib`
- **Backend:** `Flask`, `gunicorn`
- **Frontend:** `HTML`, `CSS`, `JavaScript`
- **Deployment:** Render

## 📂 Project Structure
```text
├── app/
│   ├── app.py              # Main Flask application
│   ├── templates/          # HTML templates for the UI
│   └── static/             # CSS & JS files
├── model/                  # Saved ML models (e.g., single_linear_regression.joblib)
├── data/                   # Datasets and scalers
├── src/                    # Source code for data processing and model training
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

## 🚀 How to Run Locally

### 1. Clone the repository
```bash
git clone https://github.com/your-username/Solar-Power-Generation-Prediction-using-Machine-Learning.git
cd Solar-Power-Generation-Prediction-using-Machine-Learning
```

### 2. Create a Virtual Environment (Optional but recommended)
```bash
python -m venv venv
source venv/bin/activate  # For Linux/Mac
venv\Scripts\activate     # For Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Flask App
```bash
cd app
python app.py
```
*The app will be available at `http://127.0.0.1:5000/`*

## 🌐 Deployment
This project is deployed on **Render**. The deployment uses the `gunicorn` WSGI HTTP Server.
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `cd app && gunicorn app:app`

## 🤝 Contributing
Contributions are welcome! Feel free to open an issue or submit a pull request.