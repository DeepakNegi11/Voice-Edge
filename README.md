# Voice-Edge
Many candidates struggle in interviews not due to lack of knowledge, but due to poor communication, lack of confidence, or unstructured answers.  The Voice Edge solves this problem by acting as a virtual interview coach — allowing users to record their answers and receive instant, data-driven insights on their performance

<img width="1898" height="858" alt="Screenshot (117)" src="https://github.com/user-attachments/assets/cad3b01d-6c38-435f-895d-b86ad7457dac" />

##  Features

-  **Real-time voice recording** directly in the browser
-  **ML-powered confidence scoring** using Random Forest + Gradient Boosting
-  **Audio feature extraction** using librosa (pitch, energy, pace, pauses)
-  **Grammar checking** powered by LanguageTool (100+ grammar rules, offline)
-  **Answer relevance scoring** — checks if your answer matches the question
-  **Multiple interview questions** to practice with, each scored independently
-  **Real-time dashboard** with radar chart, waveform, probability bars
-  **Actionable feedback** with specific tips to improve

---

##  Architecture
```
Browser (React — port 5173)
        ↓  audio file + question ID
Node.js / Express (port 5000)
        ↓  audio → AssemblyAI (speech-to-text)
        ↓  audio + transcript → Python ML Service
Python Flask ML Service (port 8000)
        ↓  librosa → audio features
        ↓  LanguageTool → grammar check
        ↓  keyword matching → relevance score
        ↓  scikit-learn → confidence prediction
        ↓  scorer.py → all final scores + feedback
Node.js → returns full result to React
React → renders full dashboard
```

---

## 🛠️ Technology Stack

### Frontend
| Technology | Purpose |
|---|---|
| React + Vite | User interface |
| Recharts | Radar chart, bar chart, waveform |
| Axios | HTTP requests to backend |
| MediaRecorder API | Browser-based audio capture |

### Backend
| Technology | Purpose |
|---|---|
| Node.js | Runtime environment |
| Express.js | Web server framework |
| Multer | Audio file upload handling |
| AssemblyAI API | Speech-to-text transcription |
| form-data | Forwarding files to ML service |
| dotenv | Environment variable management |

### ML Service
| Technology | Purpose |
|---|---|
| Python 3.11+ | Core ML language |
| Flask | ML microservice server |
| librosa | Audio feature extraction |
| scikit-learn | Random Forest + Gradient Boosting models |
| LanguageTool | Offline grammar checking (100+ rules) |
| numpy / pandas | Data handling |
| joblib | Model serialization |
| soundfile | Audio file reading fallback |
| ffmpeg | Audio format conversion (WebM → WAV) |

---

## 📁 Project Structure
```
interview-analyzer/
│
├── backend/                        # Node.js + Express server
│   ├── routes/
│   │   └── analyze.js              # Main API route
│   ├── services/
│   │   └── analyzer.js             # Text analysis helpers
│   ├── uploads/                    # Temp audio files (auto-created)
│   ├── .env                        # API keys (never commit this!)
│   ├── package.json
│   └── server.js                   # Entry point
│
├── frontend/                       # React + Vite app
│   ├── src/
│   │   ├── components/
│   │   │   ├── Recorder.jsx        # Audio recording + question selector
│   │   │   └── Dashboard.jsx       # Results dashboard
│   │   ├── App.jsx                 # Root component
│   │   └── index.css               # Global styles
│   ├── index.html
│   └── package.json
│
├── ml_service/                     # Python ML microservice
│   ├── training/
│   │   ├── generate_training_data.py   # Generates synthetic dataset
│   │   └── train_model.py              # Trains ML models
│   ├── models/
│   │   ├── confidence_classifier.pkl   # Trained Random Forest
│   │   └── confidence_regressor.pkl    # Trained Gradient Boosting
│   ├── app.py                      # Flask ML server entry point
│   ├── audio_features.py           # librosa feature extraction
│   ├── text_features.py            # Grammar + relevance analysis
│   ├── scorer.py                   # Score calculation + feedback
│   └── requirements.txt            # Python dependencies
│
└── README.md                       # This file
```

---

## ⚙️ Setup & Installation

### Prerequisites

Make sure you have these installed before starting:

| Software | Version | Download |
|---|---|---|
| Python | 3.11+ | https://python.org/downloads |
| Node.js | 18+ (LTS) | https://nodejs.org |
| ffmpeg | Latest | https://ffmpeg.org/download.html |


---

### Step 1 — Setup Python ML Service

Open a terminal and run:
```bash
cd ml_service
pip install -r requirements.txt
```

Download NLTK data (one time only):
```bash
python -m textblob.download_corpora
```

Generate training data and train the ML models:
```bash
python training/generate_training_data.py
python training/train_model.py
```

You should see:
```
✅ Generated 999 training samples
CV Accuracy: 0.891 ± 0.018
✅ Saved classifier → models/confidence_classifier.pkl
✅ Saved regressor  → models/confidence_regressor.pkl
🎉 Training complete!
```

---

### Step 2 — Setup Node.js Backend

Open a new terminal:
```bash
cd backend
npm install
```

Create your `.env` file:
```bash
# Create a file called .env inside the backend folder
# and paste this inside it:
PORT=5000
ASSEMBLYAI_API_KEY=your_key_here
```

> Get a free AssemblyAI API key at **https://www.assemblyai.com** (5 hours free/month)

---

### Step 3 — Setup React Frontend

Open a new terminal:
```bash
cd frontend
npm install
```

---

## 🚀 Running the Project

You need **3 terminals open simultaneously**:

### Terminal 1 — Python ML Service
```bash
cd ml_service
python app.py
```
✅ Expected output:
```
✅ LanguageTool loaded successfully!
✅ Models loaded successfully!
 * Running on http://127.0.0.1:8000
```

### Terminal 2 — Node.js Backend
```bash
cd backend
npm run dev
```
✅ Expected output:
```
✅ Backend server running at http://localhost:5000
🔑 AssemblyAI key loaded: Yes
```

### Terminal 3 — React Frontend
```bash
cd frontend
npm run dev
```
✅ Expected output:
```
Local: http://localhost:5173/
```

### Open the App
Go to **http://localhost:5173** in your browser ✅

---


<img width="1890" height="864" alt="Screenshot (115)" src="https://github.com/user-attachments/assets/ecb37266-90da-4e22-b9ad-1bb3d561162b" />


<img width="1899" height="870" alt="Screenshot (116)" src="https://github.com/user-attachments/assets/655a253e-9509-4adc-a3bc-4aa98d727d9e" />



## 📊 Scoring Breakdown

| Score | Weight | What It Measures |
|---|---|---|
| Confidence | 17% | ML prediction from vocal energy, pace, sentiment |
| Clarity | 20% | Sentence structure, vocabulary richness, filler words |
| Fluency | 15% | Speaking pace (wpm), pause ratio, smoothness |
| Delivery | 11% | Pitch variation, energy, expressiveness |
| Grammar | 15% | LanguageTool grammar rules (100+ checks) |
| Relevance | 22% | Keyword coverage vs expected answer topics |

---

## 🤖 ML Model Details

### Training Data
- **999 synthetic samples** generated with realistic distributions
- **3 balanced classes:** Low / Medium / High confidence
- **10 features** per sample (audio + text combined)

### Models
| Model | Algorithm | Purpose |
|---|---|---|
| Confidence Classifier | Random Forest (200 trees) | Predict Low/Medium/High class |
| Confidence Regressor | Gradient Boosting (200 estimators) | Predict exact 0–100 score |

### Audio Features (extracted by librosa)
- Speaking rate (words per minute)
- Pause ratio (% of silent frames)
- Pitch mean + standard deviation
- RMS energy mean + standard deviation
- Spectral centroid + rolloff
- Zero crossing rate
- MFCCs (13 coefficients)

---

## ❓ Interview Questions Available

| # | Question | Focus Area |
|---|---|---|
| 1 | Tell me about yourself | Background & experience |
| 2 | What is your greatest strength? | Self-awareness |
| 3 | What is your greatest weakness? | Self-improvement |
| 4 | Why are you interested in this role? | Motivation & fit |
| 5 | Where do you see yourself in 5 years? | Ambition & goals |
| 6 | Describe a challenging situation | Problem solving (STAR) |
| 7 | Give a teamwork example | Collaboration |
| 8 | Why should we hire you? | Value proposition |

---
