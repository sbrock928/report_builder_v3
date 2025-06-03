#!/usr/bin/env python3
"""
Setup script to create the complete project structure
"""

import os
from pathlib import Path

def create_project_structure():
    """Create the complete directory structure and __init__.py files"""
    
    # Define the directory structure
    directories = [
        "app",
        "app/core",
        "app/config", 
        "app/datawarehouse",
        "app/reporting",
        "app/reporting/models",
        "app/reporting/builders",
        "app/reporting/services",
        "app/reporting/routers",
        "frontend",
        "frontend/src",
        "frontend/src/components",
        "frontend/public"
    ]
    
    # Create directories
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Create __init__.py files
    init_files = [
        "app/__init__.py",
        "app/core/__init__.py",
        "app/config/__init__.py",
        "app/datawarehouse/__init__.py", 
        "app/reporting/__init__.py",
        "app/reporting/models/__init__.py",
        "app/reporting/builders/__init__.py",
        "app/reporting/services/__init__.py",
        "app/reporting/routers/__init__.py"
    ]
    
    for init_file in init_files:
        Path(init_file).touch()
        print(f"✅ Created: {init_file}")
    
    # Create requirements.txt
    requirements = """fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.0
python-multipart==0.0.6
python-dotenv==1.0.0
"""
    
    with open("requirements.txt", "w") as f:
        f.write(requirements)
    print("✅ Created: requirements.txt")
    
    # Create .env file
    env_content = """# SQLite Database Paths
DW_DATABASE_PATH=./data_warehouse.db
CONFIG_DATABASE_PATH=./config.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    print("✅ Created: .env")
    
    # Create frontend package.json
    package_json = """{
  "name": "reporting-frontend",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "lucide-react": "^0.263.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "devDependencies": {
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.4.14",
    "postcss": "^8.4.24"
  }
}"""
    
    with open("frontend/package.json", "w") as f:
        f.write(package_json)
    print("✅ Created: frontend/package.json")
    
    # Create frontend public/index.html
    index_html = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Data Warehouse Reporting</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>"""
    
    with open("frontend/public/index.html", "w") as f:
        f.write(index_html)
    print("✅ Created: frontend/public/index.html")
    
    print("\n🎉 Project structure created successfully!")
    print("\n📋 Next steps:")
    print("1. Copy the artifact code into the respective files")
    print("2. Run: pip install -r requirements.txt")
    print("3. Run: python -m uvicorn app.main:app --reload")
    print("4. In another terminal: cd frontend && npm install && npm start")

if __name__ == "__main__":
    create_project_structure()