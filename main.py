from pydantic import BaseModel, Field
from datetime import datetime
#from googlemaps import Client
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

# Google Maps client
#gmaps = Client(key=GOOGLE_API_KEY)

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

# Define the request model
class BatteryAlertRequest(BaseModel):
    latitude: float
    longitude: float
    direction: float
    battery_level: float = Field(..., alias="battery_percentage")


# Alert sender function
def send_low_battery_alert(lat: float, lon: float, direction: float, battery_level: float) -> bool:
    try:
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
