import requests
import json
from geopy.distance import geodesic
from geopy import Point

api_key = "9c433b72eeb618cef0e896b9646523da"
url = f"http://api.ipstack.com/check?access_key={api_key}"
response = requests.get(url)
data = json.loads(response.text)
latitude = data['latitude']
longitude = data['longitude']
print(f"Your location coordinates: {latitude}, {longitude}")

# Define the center point of the geofence and its radius in meters
geofence_center = Point(18.67340033569336, 73.88949993896484) #18.674755, 73.892306
geofence_radius = 1000  # in meters

# Define the user's current location
user_location = Point(latitude, longitude)

# Calculate the distance between the user's location and the center of the geofence
distance_to_center = geodesic(user_location, geofence_center).meters
print(distance_to_center)
# Check if the user is inside the geofence
if distance_to_center <= geofence_radius:
    print("in")
else:
    print("out")