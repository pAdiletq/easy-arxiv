from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import requests
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
from pydantic import BaseModel
from dotenv import load_dotenv
app = FastAPI()
load_dotenv()
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
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")


static_dir = Path("static")
static_dir.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static", html=True), name="static")

class HTMLFileResponse(FileResponse):
    media_type = "text/html; charset=utf-8"

@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_path = static_dir / "index.html"
    return HTMLFileResponse(html_path)
#Ai Questt
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
    text = text[:7000]  
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


#Search
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
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def extract_keywords(text: str) -> List[str]:
    try:
        common_cs_terms = load_json('data/common_cs_terms.json')
    except:
        common_cs_terms = []  
    words = text.lower().split()
    keywords = []
    for word in words:
        word = word.strip('.,!?()[]{}')
        if len(word) >= 5:  
            keywords.append(word.title())
    return list(set(keywords[:5]))

def calculate_reading_time(text: str) -> str:
    words = len(text.split())
    minutes = max(1, round(words / 30))
    minutes = 60 + round(25 + 60 * minutes / 30)
    
    hours = minutes // 60
    remaining_mins = minutes % 60
    return f"{hours}h {remaining_mins}min read"

def load_data():
    json_path = Path("/data/title.json")  
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Файл title.json не найден")
    try:
        with open(json_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Ошибка в формате JSON")

@app.get("/categories")
async def get_categories():
    data = load_data()
    return data.get("categories", [])

#Orcid
class AuthCode(BaseModel):
    code: str

class OrcidProfileRequest(BaseModel):
    pass

@app.post("/get_token")
async def get_token(data: AuthCode):
    print(f"Получен код авторизации: {data.code}")
    token_url = "https://orcid.org/oauth/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": data.code,
        "redirect_uri": REDIRECT_URI
    }
    headers = {"Accept": "application/json"}

    response = requests.post(token_url, data=payload, headers=headers)
    print("Ответ от ORCID:", response.status_code, response.text)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Ошибка получения токена")

    token_data = response.json()
    user_info_url = f"https://pub.orcid.org/v3.0/{token_data.get('orcid')}/record"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token_data.get('access_token')}"
    }
    
    user_response = requests.get(user_info_url, headers=headers)
    print("Ответ профиля от ORCID:", user_response.status_code, user_response.text)

    if user_response.status_code == 200:
        user_data = user_response.json()
        name = user_data.get("person", {}).get("name", {}).get("given-names", {}).get("value", "Неизвестный")
    else:
        name = "Неизвестный"

    return {
        "access_token": token_data.get("access_token"),
        "expires_in": token_data.get("expires_in"),
        "name": name,
        "orcid": token_data.get("orcid"),
        "refresh_token": token_data.get("refresh_token"),
        "scope": token_data.get("scope"),
        "token_type": token_data.get("token_type"),
    }

@app.post("/get_orcid_profile")
async def get_orcid_profile(data: OrcidProfileRequest):
    orcid_api_url = f"https://pub.orcid.org/v3.0/{data.orcid}"
    headers = {
        "Authorization": f"Bearer {data.access_token}",
        "Accept": "application/json"
    }

    response = requests.get(orcid_api_url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Ошибка при получении профиля")

    profile_data = response.json()
    user_name = profile_data.get("person", {}).get("name", {}).get("given-names", {}).get("value", "Неизвестный")

    return {"nickname": user_name}

@app.post("/api/orcid/callback")
async def orcid_callback(request: Request):
    data = await request.json()
    auth_code = data.get('code')
    if not auth_code:
        raise HTTPException(status_code=400, detail="Authorization code not provided")


    # Exchange the authorization code for an access token
    token_response = await httpx.post('https://orcid.org/oauth/token', data={
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': REDIRECT_URI
    })

    if token_response.status_code != 200:
        raise HTTPException(status_code=token_response.status_code, detail="Failed to fetch access token")

    token_data = token_response.json()
    access_token = token_data['access_token']

    # Fetch the user's ORCID profile
    profile_response = await httpx.get('https://pub.orcid.org/v3.0/0000-0002-1825-0097', headers={
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    })

    if profile_response.status_code != 200:
        raise HTTPException(status_code=profile_response.status_code, detail="Failed to fetch ORCID profile")

    profile_data = profile_response.json()
    nickname = profile_data['person']['name']['given-names']['value']

    return JSONResponse(content={"nickname": nickname})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)