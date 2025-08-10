# PTU_CHATBOT_SYSTEM

## 📌 Project Overview
**PTU Chatbot System** is an intelligent web-based chatbot designed to assist students of PTU with quick and accurate answers to their queries.  
It uses Machine Learning for intent classification, NLP for understanding queries, and a clean web interface for smooth interaction.

---

## ✨ Features
- 🤖 **ML-based intent classification** for accurate answers  
- 🗂 **Custom dataset (intents.json)** for university-specific queries  
- 🌐 **Flask-based web app** with HTML/CSS/JS frontend  
- 📦 **SQLite database** for storing chat history and user data  
- 📰 **PTU notice board integration** (via web scraping)  
- 📅 **Scheduler** for automated updates  
- 📤 **Email sending option** for query escalation  
- 📱 **Responsive UI** for mobile and desktop

---

## 🛠️ Tech Stack
- **Python** (Flask, NLTK, NumPy, SQLAlchemy)
- **HTML, CSS, JavaScript** (Frontend)
- **SQLite** (Database)
- **BeautifulSoup** (Web scraping)
- **NLTK + ML Model** (Intent classification)
- **Twilio API** (Optional live support notification)

---

## 📂 Project Structure
```
PTU_CHATBOT_SYSTEM/
│
├── add_notices.py        # Scrapes & updates PTU notices
├── app.py                # Main Flask server
├── chat.py               # Chat handling routes
├── data_preprocessing.py # Cleans and prepares training data
├── database_contents.txt # Sample DB data
├── ensemble_model.py     # Ensemble-based model prediction
├── init_db.py            # Database initialization
├── intents.json          # Intent dataset
├── migrate_db.py         # Database migration
├── model.py              # Model architecture
├── nltk_utils.py         # NLP helper functions
├── requirements.txt      # Dependencies
├── run.py                # Alternate app start
├── runtime.txt           # Runtime config
├── scheduler.py          # Automates notice updates & tasks
├── static/               # CSS, JS, Images
├── templates/            # HTML templates
├── train.py              # Model training script
└── utils.py              # Helper utilities
```

---

## ⚙️ Installation & Setup

### 1. Clone Repository
```bash
git clone https://github.com/vikas07-vk/PTU_CHATBOT_SYSTEM.git
cd PTU_CHATBOT_SYSTEM
```

### 2. Create Virtual Environment
```bash
python -m venv venv
```
Activate it:  
**Windows**
```bash
venv\Scripts\activate
```
**Linux/Mac**
```bash
source venv/bin/activate
```

### 3. Install Requirements
```bash
pip install -r requirements.txt
```

### 4. Initialize Database
```bash
python init_db.py
python migrate_db.py
```

### 5. Train the Model
```bash
python data_preprocessing.py
python train.py
```

### 6. Run the Application
```bash
python app.py
```
Now, open your browser and go to:
```
http://127.0.0.1:5000
```

---

## 🚀 Usage
- Enter a question in the chatbox  
- Get instant answers from the trained model  
- If the bot doesn’t know, escalate to live admin support  
- View PTU notices directly in chat  
- Optionally send query responses via email

---

## 🤝 Contributing
1. Fork the repo  
2. Create a new branch (`feature/xyz`)  
3. Commit changes  
4. Push to your fork and submit a pull request  

---

## 📜 License
This project is open-source. Add your preferred license here (MIT recommended).

---
