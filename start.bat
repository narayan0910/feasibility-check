@echo off
echo Setting up Feasibility Project...

echo Installing Backend Dependencies...
cd backend
pip install -r requirements.txt
cd ..

echo Installing Frontend Dependencies...
cd frontend
npm install
cd ..

echo Starting Servers...
start cmd /k "cd backend && python main.py"
start cmd /k "cd frontend && npm run dev"

echo Done! Backend on http://localhost:8000, Frontend check output above.
