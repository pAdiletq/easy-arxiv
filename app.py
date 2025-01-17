from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import httpx
import xml.etree.ElementTree as ET
import urllib.parse
import google.generativeai as genai
from pathlib import Path
import os
from typing import List, Dict, Any
from fastapi.middleware.gzip import GZipMiddleware
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware)

genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')

static_dir = Path("static")
static_dir.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static", html=True), name="static")

class HTMLFileResponse(FileResponse):
    media_type = "text/html; charset=utf-8"

@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_path = static_dir / "index.html"
    return HTMLFileResponse(html_path)

@app.get("/api/search") 
async def search_papers(topic: str, max_results: int = 30):
    base_url = "http://export.arxiv.org/api/query"
    query = urllib.parse.quote(f'all:"{topic}"')
    url = f"{base_url}?search_query={query}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            
        root = ET.fromstring(response.text)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        papers = []
        for entry in root.findall('atom:entry', ns):
            summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
            authors = [author.find('atom:name', ns).text for author in entry.findall('atom:author', ns)]
            if len(authors) > 3:
                authors = authors[:3] + ["et al."]
            
            paper = {
                'title': entry.find('atom:title', ns).text.strip().replace('\n', ' '),
                'authors': authors,
                'summary': summary,
                'published': entry.find('atom:published', ns).text,
                'link': next(
                    link.get('href') for link in entry.findall('atom:link', ns)
                    if link.get('type') == 'text/html'
                ),
                'pdf_link': next(
                    link.get('href') for link in entry.findall('atom:link', ns)
                    if link.get('title') == 'pdf'
                ),
                'keywords': extract_keywords(summary),
                'reading_time': calculate_reading_time(summary)
            }
            papers.append(paper)
        
        return {
            "papers": papers
        }
    
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Error fetching papers: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

def load_json(file_path: str) -> List[str]:
    with open(file_path, 'r') as file:
        return json.load(file)
    return []

def extract_keywords(text: str) -> List[str]:
    common_cs_terms = load_json('data/common_cs_terms.json')
    words = text.lower().split()
    keywords = []
    
    for word in words:
        word = word.strip('.,!?()[]{}')
        if len(word) >= 5 and (word in common_cs_terms):
            keywords.append(word.title())
    
    return list(set(keywords[:5]))

def calculate_reading_time(text: str) -> str:
    words = len(text.split())
    minutes = max(1, round(words / 30))
    minutes = 60 + round(25 + 60 * minutes / 30)
    
    hours = minutes // 60
    remaining_mins = minutes % 60
    return f"{hours}h {remaining_mins}min read"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)