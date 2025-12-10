# 📖 Final Project – Smart Information System

## 📌 Overview
This project was developed as part of the **System Engineering – Windows Final Project (Semester B 5785)**.  

The goal is to design and implement a **modern distributed information system** that includes:  
- Desktop client application (**PySide6**)  
- Application server with **FastAPI + Gateway**  
- Database hosted in the cloud (**Somee.com – SQL Server**)  
- Integration with an **AI LLM (Ollama + RAG)** for consulting and recommendations  

👉 The chosen domain: **[💡 adjust here: e.g., Recipe Management (CookSmart) / Smart Trip Planner]**

---

## 🏗️ Architecture
The system follows a **multi-tier architecture**:

### Frontend (Client)
- Desktop application built with **PySide6**  
- Implements **MVP + Microfrontends**  
- Views include:
  - Login / Register  
  - Search  
  - Detail View (Recipe/Trip)  
  - Add New Item  
  - Favorites  
  - AI Consultation  
- Visualizations with **QtCharts**

### Backend (Server)
- Built with **FastAPI**  
- Organized using **CQRS/MVC**  
- Routers for users, search, favorites, AI, external APIs  
- Gateway pattern for external service calls (e.g., weather, OpenTripMap, recipe APIs)

### Database
- Hosted on **Somee.com (SQL Server)**  
- Implements **Event Sourcing** for tracking changes

### AI Integration
- **Ollama running in Docker**  
- Implements **RAG (Retrieval-Augmented Generation)**  
- `/ai/ask` endpoint for AI consultation

---

## ⚙️ Installation & Setup

### 1. Clone Repository
```bash
git clone https://github.com/<your-org>/<your-repo>.git
cd <your-repo>
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.api.main:app --reload
```

### 3. Frontend Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python frontend/main.py
```

### 4. Database
- Hosted on **Somee.com (SQL Server)**  
- Configure connection string in `.env`:
```env
SQLSERVER_CONN_STR="Driver={ODBC Driver 17 for SQL Server};Server=...;Database=...;UID=...;PWD=..."
```

### 5. Ollama (AI Agent)
- Install Docker and Ollama  
- Run Ollama server in container:
```bash
docker run -d -p 11434:11434 ollama/ollama
```
- Test with:
```bash
curl http://localhost:11434/api/tags
```

---

## 🚀 Features
- ✅ User registration & login with authentication (JWT)  
- ✅ Search data in the chosen domain  
- ✅ View detailed information for results  
- ✅ Visualize data in graphs and tables (QtCharts)  
- ✅ Consult with AI agent (RAG with Ollama)  
- ✅ Add new entries (e.g., add recipe, add trip)  
- ✅ Favorites management  
- ✅ Cloud database with Event Sourcing  

---

## 🛠️ Tech Stack
- **Frontend:** PySide6, QtCharts  
- **Backend:** FastAPI, CQRS/MVC  
- **Database:** SQL Server (Somee.com)  
- **AI Integration:** Ollama (Docker), RAG  
- **Patterns:** MVP, Microfrontends, Gateway  
- **Version Control:** GitHub  

---

## 📂 Project Structure
```
.
├── backend/
│   ├── api/            # FastAPI routers
│   ├── services/       # Business logic
│   ├── models/         # Database models
│   ├── db/             # Database config
│   └── main.py         # FastAPI entrypoint
├── frontend/
│   ├── views/          # PySide6 views (MVP)
│   ├── presenters/     # Presenters
│   ├── utils/          # Shared utilities
│   └── main.py         # Application entrypoint
└── README.md
```

---

## 📊 Non-Functional Requirements
- Desktop Application with PySide6  
- MVP + Microfrontends design  
- Charts with QtCharts  
- Backend with FastAPI & CQRS/MVC  
- Event Sourcing with SQL Server on Somee.com  
- Gateway pattern for external APIs  
- AI integration with Ollama (Docker) using RAG  
- Code versioned on GitHub  
- Optional: Cloudinary for image hosting  

---

## 👥 Authors
- Naama Leah
- Ester Dray

---

