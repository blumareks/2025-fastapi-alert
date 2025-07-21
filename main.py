from pydantic import BaseModel, Field

from datetime import datetime, timedelta
from googlemaps import Client
import requests
import logging
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

load_dotenv()

# Configuration
GOOGLE_API_KEY = os.environ["GOOGLEMAPS_API_KEY"]  # set in your environment
ALERT_API_URL = "https://example.com/alert-endpoint"
MCP_SERVER_URL = "https://mcp.example.com/reasoning"  # hypothetical

# State management
state = {
    "charge_ok": True,
    "time_received": None,
    "location": None
}

# Define request model
class BatteryAlertRequest(BaseModel):
    latitude: float
    longitude: float
    direction: float
    battery_level: float = Field(..., alias="battery_percentage")

def set_low_battery_state(lat, lon):
    state["charge_ok"] = False
    state["time_received"] = datetime.now()
    state["location"] = (lat, lon)
    

# Google Maps client
gmaps = Client(key=GOOGLE_API_KEY)

# address = '1600 Amphitheatre Parkway, Mountain View, CA'
# geocode_result = gmaps.geocode(address)
# if geocode_result:
#     location = geocode_result[0]['geometry']['location']
#     print(f"Latitude: {location['lat']}, Longitude: {location['lng']}")

# Initialize FastAPI
app = FastAPI()
api_key_header = APIKeyHeader(name="X-API-KEY")
async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != os.environ["SECURITY_API_KEY"]:
        raise HTTPException(
            status_code=403,
            detail="Invalid API Key"
        )
    return api_key


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace with the actual URL where the alert should be sent
ALERT_API_URL = "https://example.com/alert-endpoint"

# # Define the request model
# class BatteryAlertRequest(BaseModel):
#     latitude: float
#     longitude: float
#     direction: float
#     battery_level: float = Field(..., alias="battery_percentage")


# Alert sender function
def send_low_battery_alert(lat: float, lon: float, direction: float, battery_level: float) -> bool:
    try:
        set_low_battery_state(lat, lon)

        payload = {
            "latitude": lat,
            "longitude": lon,
            "direction": direction,
            "battery_percentage": battery_level,
            "timestamp": datetime.now().isoformat()
        }
        response = requests.post(ALERT_API_URL, json=payload)
        #response.raise_for_status()
        logger.info(f"Successfully sent low battery alert: {battery_level}%")
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to send alert: {e}")
        return False

def find_nearest_charger(lat, lon):
    places = gmaps.places_nearby(location=(lat, lon), radius=5000, keyword="EV charger")
    if places['results']:
        charger = places['results'][0]
        """
        {'destination_addresses': ['2860 16th St, San Francisco, CA 94103, USA'], 'origin_addresses': ['5911 US-101, San Francisco, CA 94103, USA'], 
        'rows': 
        [{'elements': 
        [{'distance': {'text': '1.2 km', 'value': 1218}, 
        'duration': {'text': '5 mins', 'value': 295}, 'status': 'OK'}]}], 
        'status': 'OK'}"""
        distance_mtx = gmaps.distance_matrix((lat, lon), charger["geometry"]["location"], mode="driving")
        time_to = distance_mtx["rows"][0]["elements"][0]["duration"]["text"]
        print(time_to)
        distance_to = distance_mtx["rows"][0]["elements"][0]["distance"]["value"]
        print(distance_to)
        return {
            "name": charger['name'],
            "distance_km": distance_to,#1.0  # Simplified: real distance calculation can use gmaps.distance_matrix
            "time_to":time_to
        }
    return {"name": "Unknown", "distance_km": "Unknown", "time_to":"unknown"}


# Use global state variable for simplicity (replace with DB or cache in production)
malfunction_state = {"active": False}

@app.post("/battery-malfunction/on")
def battery_malfunction_on():
    malfunction_state["active"] = True
    return {"status": "malfunction_on"}

@app.post("/battery-malfunction/off")
def battery_malfunction_off():
    malfunction_state["active"] = False
    return {"status": "malfunction_off"}


@app.get("/charge-status")
def get_charge_status():
    if not state["charge_ok"] and state["time_received"]:
        elapsed = datetime.now() - state["time_received"]
        if elapsed > timedelta(minutes=5):
            state["charge_ok"] = True
            state["time_received"] = None
            state["location"] = None

    malfuntion_text = ""

    if malfunction_state["active"]:
        malfuntion_text = "There is an DTC malfunction code P0AFA active - it is for High-voltage battery system voltage imbalance.  To remedy it please go to a nearest service shop to undertake the software update for improved cell-balancing logic."


    if state["charge_ok"]:
        return {"message": "Your vehicle charge is okay. "+ malfuntion_text}
    else:
        state["charge_ok"] = True
        lat, lon = state["location"]
        charger = find_nearest_charger(lat, lon)
        return {"message": f"Your battery charge is below 20%, recharge shortly -- I've looked nearby stations and the closest is {charger['name']}, {charger['time_to']} and {int(int(charger['distance_km'])*0.00062137*10)/10} miles away. "+ malfuntion_text}


# Function to get shortest route to nearest EV charger
def get_route_to_nearest_charger(lat: float, lon: float):
    try:
        # Step 1: Find nearby EV chargers
        # places_result = gmaps.places_nearby(
        #     location=(lat, lon),
        #     radius=10000,  # 10 km
        #     keyword="EV charger"
        # )
        
        # if not places_result.get("results"):
        #     logger.warning("No chargers found nearby")
        #     return {"message": "No chargers found nearby"}

        # nearest = places_result["results"][0]
        # charger_location = nearest["geometry"]["location"]
        # charger_name = nearest.get("name", "EV Charger")

        # Step 2: Get shortest route to charger
        # directions = gmaps.directions(
        #     origin=(lat, lon),
        #     destination=(charger_location["lat"], charger_location["lng"]),
        #     mode="driving"
        # )

        # return {
        #     "destination": charger_name,
        #     "route_summary": directions[0]["summary"] if directions else "Route unavailable",
        #     "steps": [
        #         step["html_instructions"] for step in directions[0]["legs"][0]["steps"]
        #     ] if directions else []
        # }
        return {
            "destination": f"ev charger closest to me {(lat, lon)}",
            "route_summary": "provide the final route to available and powered EV charger",
            "steps": "find next charger"}



    except Exception as e:
        logger.error(f"Error finding route: {e}")
        return {"message": f"Error finding route: {str(e)}"}




# API endpoint
"""
{
  "latitude": 37.7749,
  "longitude": -122.4194,
  "direction": 180.0,
  "battery_percentage": 12.5
}
"""
@app.post("/low-battery-alert")
def receive_low_battery_alert(alert: BatteryAlertRequest, api_key: str = Depends(get_api_key)):
    success = send_low_battery_alert(
        lat=alert.latitude,
        lon=alert.longitude,
        direction=alert.direction,
        battery_level=alert.battery_level
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to send low battery alert to external service")

    
    # Get shortest route to charger
    route_info = get_route_to_nearest_charger(alert.latitude, alert.longitude)

    return {
        "message": "Alert sent and route computed",
        "route": route_info
    }

#example response
"""
{
  "message": "Alert sent and route computed",
  "route": {
    "destination": "ChargePoint Charging Station",
    "route_summary": "I-280 N",
    "steps": [
      "Head north on Main St",
      "Turn right onto I-280 N ramp",
      "Take exit 23 for El Camino Real"
    ]
  }
}
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)
