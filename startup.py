"""
Simple startup script for the reporting system
"""
import subprocess
import sys
import os
import time
from pathlib import Path

def check_python():
    """Check if Python is available"""
    try:
        result = subprocess.run([sys.executable, '--version'], capture_output=True, text=True)
        print(f"✅ Python found: {result.stdout.strip()}")
        return True
    except Exception:
        print("❌ Python not found")
        return False

def check_node():
    """Check if Node.js is available"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        print(f"✅ Node.js found: {result.stdout.strip()}")
        return True
    except Exception:
        print("❌ Node.js not found. Please install Node.js from https://nodejs.org/")
        return False

def install_python_deps():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        print("✅ Python dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install Python dependencies")
        return False

def install_node_deps():
    """Install Node.js dependencies"""
    print("📦 Installing Node.js dependencies...")
    frontend_path = Path('frontend')
    if not frontend_path.exists():
        print("❌ Frontend directory not found")
        return False
    
    try:
        subprocess.run(['npm', 'install'], cwd=frontend_path, check=True)
        print("✅ Node.js dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install Node.js dependencies")
        return False

def start_backend():
    """Start the FastAPI backend"""
    print("🚀 Starting FastAPI backend...")
    try:
        process = subprocess.Popen([
            sys.executable, '-m', 'uvicorn', 
            'app.main:app', '--reload', '--host', '0.0.0.0', '--port', '8000'
        ])
        time.sleep(3)  # Give backend time to start
        print("✅ Backend started on http://localhost:8000")
        return process
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def start_frontend():
    """Start the React frontend"""
    print("🚀 Starting React frontend...")
    frontend_path = Path('frontend')
    if not frontend_path.exists():
        print("❌ Frontend directory not found")
        return None
    
    try:
        process = subprocess.Popen(['npm', 'start'], cwd=frontend_path)
        time.sleep(3)  # Give frontend time to start
        print("✅ Frontend starting on http://localhost:3000")
        return process
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def main():
    print("🔄 Starting Data Warehouse Reporting System")
    print("=" * 50)
    
    # Check prerequisites
    if not check_python():
        sys.exit(1)
    
    if not check_node():
        sys.exit(1)
    
    # Install dependencies
    if not install_python_deps():
        sys.exit(1)
    
    if not install_node_deps():
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🚀 Starting services...")
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        sys.exit(1)
    
    # Start frontend
    frontend_process = start_frontend()
    if not frontend_process:
        backend_process.terminate()
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ System is running!")
    print("📊 Frontend: http://localhost:3000")
    print("🔧 Backend API: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("💾 Database Stats: http://localhost:8000/api/database/stats")
    print("\nPress Ctrl+C to stop all services")
    
    try:
        # Wait for processes
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        backend_process.terminate()
        frontend_process.terminate()
        print("✅ All services stopped")

if __name__ == "__main__":
    main()