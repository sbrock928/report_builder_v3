# Quick Start Guide (README.md)
# Data Warehouse Reporting System - Quick Start

## 🚀 Super Simple Setup (SQLite)

### Prerequisites
- Python 3.9+ (`python --version`)
- Node.js 16+ (`node --version`)

### Option 1: One-Command Start
```bash
python startup.py
```

### Option 2: Manual Start

1. **Install Python Dependencies:**
```bash
pip install -r requirements.txt
```

2. **Start Backend:**
```bash
python -m uvicorn app.main:app --reload
```

3. **Install Frontend Dependencies (new terminal):**
```bash
cd frontend
npm install
```

4. **Start Frontend:**
```bash
npm start
```

### 🎯 Access Points
- **Frontend UI:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Database Stats:** http://localhost:8000/api/database/stats

### 📊 Sample Data Included
The system automatically creates:
- **3 sample deals** (101, 102, 103)
- **9 sample tranches** (A, B, C combinations)
- **36 tranche balance records** (4 cycles each)
- **10 default calculations** ready to use

### 🔧 What You Can Do
1. **Report Builder:** Generate reports with deal/tranche filtering
2. **Calculation Builder:** Create custom financial calculations
3. **Data Management:** Full CRUD operations on calculations

### 📁 Database Files
- `data_warehouse.db` - Contains deals, tranches, financial data
- `config.db` - Contains calculations, templates, execution logs

### 🛠️ Development
- Backend auto-reloads on code changes
- Frontend hot-reloads on code changes
- Both databases are automatically created and seeded

### ❓ Troubleshooting
- **Port conflicts:** Change ports in `.env` file
- **Database issues:** Delete `.db` files and restart
- **Dependencies:** Run `pip install --upgrade -r requirements.txt`