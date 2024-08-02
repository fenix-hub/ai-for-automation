import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Client:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.tomtom.com"

    def get_route_summary(self, start, end, departure_time):
        endpoint = "/routing/1/calculateRoute/{start}:{end}/json".format(start=start, end=end)
        url = self.base_url + endpoint
        params = {
            "departAt": departure_time.strftime('%Y-%m-%dT%H:%M:%S'),
            "sectionType": "traffic",
            "report": "effectiveSettings",
            "traffic": "true",
            "travelMode": "car",
            "computeTravelTimeFor": "all",
            "key": self.api_key
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get("routes"):
                summary = data["routes"][0]["summary"]
                summary["points"] = data["routes"][0]["legs"][0]["points"]
                return summary
        raise Exception(f"{response.status_code} - {response.text}")
        return None        


    def get_location(self, address):
        endpoint = "/search/2/geocode/{address}.json".format(address=address)
        url = self.base_url + endpoint
        params = {
            "key": self.api_key
        }
        response = requests.get(url, params=params)
        print(response.json())
        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                return data["results"][0]["position"]
        return response.json()