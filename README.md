# 2025-fastapi-alert
small microservice to alert EV driver about battery and give them directions to the closest charger

## Run the app:
Install FastAPI and Uvicorn if you haven’t:
```
python3 -m venv .venv                                   
source .venv/bin/activate                            
pip3 install -r requirements.txt 
```
Then run it:
```
uvicorn main:app --reload
```