#!/usr/bin/env python3
"""
Setup and verification script for Flask Task Manager
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("ERROR: Python 3.8 or higher is required")
        return False
    print(f"OK: Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def check_virtual_environment():
    """Check if running in virtual environment"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("OK: Running in virtual environment")
        return True
    print("WARNING: Not running in virtual environment (recommended)")
    return True

def install_dependencies():
    """Install required dependencies"""
    try:
        print("Installing dependencies...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("OK: Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("ERROR: Failed to install dependencies")
        return False

def create_env_file():
    """Create .env file from example if it doesn't exist"""
    if not Path('.env').exists():
        if Path('.env.example').exists():
            import shutil
            shutil.copy('.env.example', '.env')
            print("OK: Created .env file from .env.example")
        else:
            with open('.env', 'w') as f:
                f.write("SECRET_KEY=dev-secret-key-change-in-production\n")
                f.write("FLASK_ENV=development\n")
                f.write("DATABASE_URL=sqlite:///tasks.db\n")
            print("OK: Created basic .env file")
        return True
    print("OK: .env file already exists")
    return True

def test_import():
    """Test if the application can be imported"""
    try:
        from ARIA.artifacts.code.app import create_app
        app = create_app('testing')
        print("OK: Application imports successfully")
        return True
    except Exception as e:
        print(f"ERROR: Failed to import application: {e}")
        return False

def run_tests():
    """Run the test suite"""
    try:
        print("Running tests...")
        result = subprocess.run([sys.executable, 'tests.py'], capture_output=True, text=True)
        if result.returncode == 0:
            print("OK: All tests passed")
            return True
        else:
            print("ERROR: Some tests failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"ERROR: Failed to run tests: {e}")
        return False

def main():
    """Main setup function"""
    print("Flask Task Manager Setup\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Virtual Environment", check_virtual_environment),
        ("Dependencies", install_dependencies),
        ("Environment File", create_env_file),
        ("Application Import", test_import),
        ("Test Suite", run_tests)
    ]
    
    failed_checks = []
    
    for name, check_func in checks:
        print(f"\nChecking {name}...")
        if not check_func():
            failed_checks.append(name)
    
    print("\n" + "="*50)
    if not failed_checks:
        print("Setup completed successfully!")
        print("\nNext steps:")
        print("1. Run 'python app.py' to start the development server")
        print("2. Open http://localhost:5000 in your browser")
        print("3. Login with admin/admin123")
    else:
        print("Setup completed with issues:")
        for check in failed_checks:
            print(f"   - {check}")
        sys.exit(1)

if __name__ == '__main__':
    main()