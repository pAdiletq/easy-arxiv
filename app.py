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
import io
import PyPDF2

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

@app.get("/ai_quest", response_class=HTMLResponse)
async def ai_quest_open(pdf: str):
    pdf_bytes = await download_pdf(pdf)
    pdf_text = extract_text_from_pdf(pdf_bytes)
    html_path = static_dir / "ai_quest.html"
    
    with open(html_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    try:
        flashcards = await get_ai_highlights(pdf_text)
        questions = await get_ai_quiz_questions(flashcards)
    except Exception as e:
        print('Error:', e)
        flashcards = []
        questions = []

    html_content = html_content.replace("{{pdf_text}}", pdf_text)
    html_content = html_content.replace("{{pdf_link}}", pdf)
    html_content = html_content.replace("{{flashcards}}", json.dumps(flashcards))
    html_content = html_content.replace("{{questions}}", json.dumps(questions))

    return HTMLResponse(content=html_content, status_code=200)

@app.get("/api/getPaperData")
async def get_paper_data(pdf: str):
    pdf_bytes = await download_pdf(pdf)
    pdf_text = extract_text_from_pdf(pdf_bytes)
    
    try:
        flashcards = await get_ai_highlights(pdf_text)
        questions = await get_ai_quiz_questions(flashcards)
    except Exception as e:
        print('Error:', e)
        flashcards = []
        questions = []

    return {
        "pdf_text": pdf_text,
        "flashcards": flashcards,
        "questions": questions
    }

async def get_ai_highlights(text: str) -> List[Dict[str, Any]]:
    text = text[:7000]  # Limit to 7000 characters
    system_prompt = f'''
    Generate 9 interactive flashcard contents based on the highlights of the following text:\n
    {text}\n\n
    Output should be clearly in JSON format without any additional text and sybmols like "`" before and after the JSON object!!!\n
    FORMAT:
    {{
        "flashcards": [
            {{"topic #1": "content #1"}},
            {{"topic #2": "content #2"}},
            {{"topic #3": "content #3"}},
            {{"topic #4": "content #4"}},
            {{"topic #5": "content #5"}},
            {{"topic #6": "content #6"}},
            {{"topic #7": "content #7"}},
            {{"topic #8": "content #8"}},
            {{"topic #9": "content #9"}}
        ]
    }}
    '''
    response = model.generate_content(system_prompt).text
    print(response)
    flashcards = json.loads(response)
    return flashcards

async def get_ai_quiz_questions(flashcards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    system_prompt = f'''
    Generate 9 multiple choice questions based on the following flashcard contents:\n
    {json.dumps(flashcards)}\n\n
    Output should be clearly in JSON format without any additional text and sybmols like "`" before and after the JSON object!!!\n
    FORMAT:
    {{
        "questions": [
            "q1": {{
                "question": "What is the question?",
                "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
                "answer": 0
            }},
            "q2": {{
                "question": "What is the question?",
                "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
                "answer": 1
            }},
            "q3": {{
                "question": "What is the question?",
                "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
                "answer": 2
            }},
            ...
    }}
    '''
    response = model.generate_content(system_prompt).text
    print(response)
    questions = json.loads(response)
    return questions


async def download_pdf(pdf_url: str) -> bytes:
    """Download PDF from URL and return raw bytes."""
    async with httpx.AsyncClient() as client:
        response = await client.get(pdf_url)
        response.raise_for_status()
        return response.content
    
def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text content from PDF bytes."""
    pdf_file = io.BytesIO(pdf_bytes)
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

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
    uvicorn.run(app, host="127.0.0.1", port=5000)