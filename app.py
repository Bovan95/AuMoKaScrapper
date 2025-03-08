from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import ScrapeMobile

app = FastAPI(title="Mobile.de Scraper API", 
              description="API for scraping car listings from mobile.de",
              version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/", response_model=dict)
async def root():
    return {
        "message": "Mobile.de Scraper API",
        "version": "1.0.0",
        "endpoints": [
            "/search - Search for vehicles",
            "/makes - Get list of available makes"
        ]
    }

@app.get("/search", response_model=ScrapeMobile.SearchResponse)
async def search_cars(
    make: str = Query(..., description="Vehicle make (manufacturer)"),
    model: Optional[str] = Query(None, description="Vehicle model"),
    min_price: Optional[int] = Query(None, description="Minimum price"),
    max_price: Optional[int] = Query(None, description="Maximum price"),
    min_year: Optional[int] = Query(None, description="Minimum registration year"),
    max_year: Optional[int] = Query(None, description="Maximum registration year"),
    page: int = Query(1, description="Page number")
):
    # Build the URL for the search
    url = ScrapeMobile.build_search_url(
        make=make,
        model=model,
        min_price=min_price,
        max_price=max_price,
        min_year=min_year,
        max_year=max_year,
        page=page
    )
    
    # Scrape the data
    return ScrapeMobile.scrape_mobile_de(url)

@app.get("/makes", response_model=List[dict])
async def get_makes():
    return ScrapeMobile.get_makes()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)