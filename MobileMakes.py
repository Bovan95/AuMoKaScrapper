from pydantic import BaseModel
from typing import List, Optional
import httpx
import ScrapeMobile

class MobileMakes:
    _instance = None
    _makes_list = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MobileMakes, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def parse_make_options(self):
        """
        Parse the make options from mobile.de HTML content.
            
        Returns:
            dict: Dictionary mapping make names to their IDs
        """

        MOBILE_DE_URL = "https://m.mobile.de/consumer/api/search/reference-data/filters/Car"

        try:
            with httpx.Client() as client:
                response = client.get(MOBILE_DE_URL, headers=ScrapeMobile.get_headers())
                response.raise_for_status()
                data = response.json()

            # Extract 'ms' from the correct location
            ms_data = data.get('data', {}).get('ms', [])
            ms_hash_table = {item["i"]: item["n"] for item in ms_data}

            return ms_hash_table
        
        except httpx.HTTPStatusError as e:
            print(f"HTTP error: {e.response.status_code}")
        except Exception as e:
            print(f"Error: {str(e)}")
        
    def get_makes(self):
        """
        Return the dictionary of makes for use in the API.
        This function should be called during application startup.
        
        Returns:
            list: List of dictionaries with make ID and name
        """
        if self._makes_list is None:
            makes_dict = self.parse_make_options()
            # Convert to list format for API
            self._makes_list = [{"id": make_id, "name": make_name} for make_name, make_id in makes_dict.items()]
        
        return self._makes_list