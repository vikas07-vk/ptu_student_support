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

## Preview
![ptu front page](https://github.com/user-attachments/assets/47f4a966-eaa0-4615-a4ef-7ddc21afd934)
![photo_2025-08-30_15-03-31](https://github.com/user-attachments/assets/bc4529f8-a668-4393-8261-e101d7330ae8)
![photo_2025-08-30_15-03-47](https://github.com/user-attachments/assets/ae16a504-53f5-4563-994a-b67360277eaa)
![photo_2025-08-30_15-03-57](https://github.com/user-attachments/assets/127e5977-58c4-481f-b247-5a6e431115cd)
![photo_2025-08-30_15-04-08](https://github.com/user-attachments/assets/50fd3900-2b03-4255-a252-c76084a3c7f1)
<h3>Chatbot</h3>
![photo_2025-08-30_15-04-04](https://github.com/user-attachments/assets/d70b01a0-7f2a-4e99-8486-0ceeecc34cc8)
![photo_2025-08-30_15-04-01](https://github.com/user-attachments/assets/84457b5e-74e6-4883-9d91-efda0ed30d52)

---

## 📜 License
This project is open-source. Add your preferred license here (MIT recommended).

---
