from pydantic import BaseModel
from typing import List, Optional
import httpx
import ScrapeMobile

class MobileMakes:
    _instance = None
    _makes_hash = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MobileMakes, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def get_makes_hash(self):
        """
        Parse the make options from mobile.de HTML content.
            
        Returns:
            dict: Dictionary mapping make names to their IDs
        """
        if self._makes_hash is None:
            MOBILE_DE_URL = "https://m.mobile.de/consumer/api/search/reference-data/filters/Car"

            try:
                with httpx.Client() as client:
                    response = client.get(MOBILE_DE_URL, headers=ScrapeMobile.get_headers())
                    response.raise_for_status()
                    data = response.json()

                # Extract 'ms' from the correct location
                ms_data = data.get('data', {}).get('ms', [])
                self._makes_hash = {item["n"] : item["i"]  for item in ms_data}
            
            except httpx.HTTPStatusError as e:
                print(f"HTTP error: {e.response.status_code}")
            except Exception as e:
                print(f"Error: {str(e)}")
        return self._makes_hash
        
    def get_makes(self):
        """
        Return the dictionary of makes for use in the API.
        This function should be called during application startup.
        
        Returns:
            list: List of dictionaries with make ID and name
        """
        makes_dict = self.get_makes_hash()
        # Convert to list format for API
        return [{"id": make_id, "name": make_name} for make_name, make_id in makes_dict.items()]