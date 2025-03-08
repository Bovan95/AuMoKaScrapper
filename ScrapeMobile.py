import requests
from bs4 import BeautifulSoup
from fastapi import HTTPException
from pydantic import BaseModel
from typing import List, Optional
from MobileMakes import MobileMakes
import random
import time

# List of User-Agents to rotate
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Mobile/15E148 Safari/604.1"
]

mobile_makes_instance = MobileMakes()

# Output model
class CarListing(BaseModel):
    title: str
    price: str
    year: Optional[str] = None
    mileage: Optional[str] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    power: Optional[str] = None
    location: Optional[str] = None
    url: str
    image_url: Optional[str] = None

class SearchResponse(BaseModel):
    total_results: int
    page: int
    results: List[CarListing]

def get_headers(): #todo create utils
    return {
        "User-Agent": random.choice(user_agents),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Referer": "https://www.mobile.de/",
    }

def build_search_url(make: str, model: Optional[str] = None, 
                    min_price: Optional[int] = None, max_price: Optional[int] = None,
                    min_year: Optional[int] = None, max_year: Optional[int] = None,
                    page: int = 1):
    base_url = "https://suchen.mobile.de/fahrzeuge/search.html"
    
    params = {
        "isSearchRequest": "true",
        "s": "Car",  # Cars
        "pageNumber": page
    }
    
    # Add make (mandatory)
    params["makeModelVariant1.makeId"] = make
    
    # Add optional model
    if model:
        params["makeModelVariant1.modelId"] = model
    
    # Add price range
    if min_price:
        params["minPrice"] = min_price
    if max_price:
        params["maxPrice"] = max_price
        
    # Add year range
    if min_year:
        params["minFirstRegistrationDate"] = min_year
    if max_year:
        params["maxFirstRegistrationDate"] = max_year
    
    # Construct URL with parameters
    url = base_url
    query_params = []
    for key, value in params.items():
        query_params.append(f"{key}={value}")
    
    if query_params:
        url += "?" + "&".join(query_params)
    
    return url

def scrape_mobile_de(url: str) -> SearchResponse:
    
    # Add a small delay to avoid aggressive scraping
    time.sleep(random.uniform(0.5, 1.5))
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract the total number of results
    total_results = 0
    result_count_elem = soup.select_one('span.result-count')
    if result_count_elem:
        try:
            total_results = int(result_count_elem.text.strip().replace(',', '').split()[0])
        except (ValueError, IndexError):
            total_results = 0
    
    # Get the current page number
    current_page = 1
    pagination_elem = soup.select_one('li.pagination-item.pagination-item--current')
    if pagination_elem:
        try:
            current_page = int(pagination_elem.text.strip())
        except ValueError:
            current_page = 1
    
    # Extract car listings
    car_listings = []
    
    # This selector needs to be adjusted based on mobile.de's actual HTML structure
    listing_elements = soup.select('div.cBox-body.cBox-body--resultitem')
    
    for listing in listing_elements:
        try:
            # Extract title
            title_elem = listing.select_one('span.h3')
            title = title_elem.text.strip() if title_elem else "Unknown Title"
            
            # Extract URL
            url_elem = listing.select_one('a.link--muted')
            url = "https://www.mobile.de" + url_elem['href'] if url_elem and 'href' in url_elem.attrs else ""
            
            # Extract price
            price_elem = listing.select_one('span.price-block')
            price = price_elem.text.strip() if price_elem else "Price not available"
            
            # Extract image URL
            img_elem = listing.select_one('img.imagebox__image')
            image_url = img_elem['src'] if img_elem and 'src' in img_elem.attrs else None
            
            # Extract details
            details = {}
            detail_items = listing.select('div.vehicle-data')
            
            for item in detail_items:
                detail_text = item.text.strip()
                
                if "km" in detail_text:
                    details['mileage'] = detail_text
                elif any(year in detail_text for year in ['/20', '/19']):  # Common year prefixes
                    details['year'] = detail_text
                elif any(fuel in detail_text.lower() for fuel in ['petrol', 'diesel', 'electric', 'hybrid']):
                    details['fuel_type'] = detail_text
                elif any(trans in detail_text.lower() for trans in ['automatic', 'manual']):
                    details['transmission'] = detail_text
                elif 'kw' in detail_text.lower() or 'hp' in detail_text.lower():
                    details['power'] = detail_text
            
            # Extract location
            location_elem = listing.select_one('div.seller-info__address')
            location = location_elem.text.strip() if location_elem else None
            
            car_listing = CarListing(
                title=title,
                price=price,
                url=url,
                image_url=image_url,
                year=details.get('year'),
                mileage=details.get('mileage'),
                fuel_type=details.get('fuel_type'),
                transmission=details.get('transmission'),
                power=details.get('power'),
                location=location
            )
            
            car_listings.append(car_listing)
            
        except Exception as e:
            # Skip this listing if there's an error
            continue
    
    return SearchResponse(
        total_results=total_results,
        page=current_page,
        results=car_listings
    )

def get_makes():
    return mobile_makes_instance.get_makes()