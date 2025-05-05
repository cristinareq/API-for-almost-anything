import streamlit as st
import requests
import json
import openai
import os
import pandas as pd
from bs4 import BeautifulSoup, Comment
import re
from streamlit_option_menu import option_menu
import secrets
import base64
from dotenv import load_dotenv

# for local dev only—loads .env into os.environ
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY")

# if you ever need to override the listening port, you can
PORT = int(os.getenv("PORT", 5001))


# Config and styling
st.set_page_config(
    page_title="Web Scraper API Generator",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for improved styling
def load_css():
    st.markdown("""
    <style>
        .main {
            background-color: #f5f7f9;
        }

        /* Global left padding for all content */
        .block-container {
            padding-left: 150px !important;
            padding-right: 100px !important;
        }

        /* Make general text larger */
        div[data-testid="stMarkdownContainer"] p,
        div[data-testid="stMarkdownContainer"] li,
        div[data-testid="stMarkdownContainer"] span,
        div[data-testid="stMarkdownContainer"] {
            font-size: 18px !important;
            line-height: 1.7;
        }

        /* Make headers larger */
        h1 {
            font-size: 48px !important;
        }

        h2 {
            font-size: 36px !important;
        }

        h3 {
            font-size: 28px !important;
        }

        /* Optional: override your custom header classes */
        .header-text {
            font-size: 55px;
            font-weight: 700;
            color: #1e3a8a;
        }

        .subheader-text {
            font-size: 36px;
            font-weight: 500;
            color: #475569;
        }

        /* Buttons */
        .stButton button {
            background-color: #4c78a8;
            color: white;
            border-radius: 5px;
            padding: 12px 20px;
            font-weight: 500;
            font-size: 17.6px;
        }

        .stButton button:hover {
            background-color: #3a5c85;
        }

        /* Card components */
        .card, .success-card, .warning-card {
            border-radius: 10px;
            padding: 24px;
            margin-bottom: 16px;
        }

        .card {
            background-color: white;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .success-card {
            background-color: #d1fae5;
            border-left: 4px solid #059669;
        }

        .warning-card {
            background-color: #fef3c7;
            border-left: 4px solid #d97706;
        }

        /* Navigation */
        .nav-link, .nav-link-selected {
            font-size: 18px !important;
            padding: 12px 20px !important;
        }
    </style>
    """, unsafe_allow_html=True)


load_css()

# --- User-responsibility disclaimer (shows on every page) ---
st.sidebar.info(
    "**Disclaimer**\n\n"
    "You are solely responsible for any data you collect with this tool. "
    "Scrape responsibly and comply with all applicable laws, robots.txt directives, "
    "and the target site's terms of service."
)

# OpenAI API key handling
def load_api_key():
    # Get API key from environment variable
    return os.environ.get('OPENAI_API_KEY', '')

def set_openai_key():
    api_key = load_api_key()
    if api_key:
        openai.api_key = api_key
        return True
    return False

# Navigation
def navigation():
    options = ["Home", "Extract", "Results", "Merge Code"]
    default_page = st.session_state.get("page", "Home")
    default_index = options.index(default_page) if default_page in options else 0

    selected = option_menu(
        menu_title=None,
        options=options,
        icons=["house", "magic", "code-slash", "arrow-repeat"],
        menu_icon="cast",
        default_index=default_index,  
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#f8fafc"},
            "icon": {"color": "#4c78a8", "font-size": "18px"},
            "nav-link": {"font-size": "18px", "text-align": "center", "margin": "0px", "--hover-color": "#ebedf0", "padding": "12px 20px"},
            "nav-link-selected": {"background-color": "#4c78a8", "color": "white", "font-size": "18px", "padding": "12px 20px"},
        }
    )
    return selected


# Home page
def home_page():
    
    st.markdown("<h1 class='header-text'>Natural Language API Generator</h1>", unsafe_allow_html=True)
    st.markdown("<h2 class='subheader-text'>Turn any public web page into a FastAPI endpoint in minutes</h2>", unsafe_allow_html=True)

    spacer, col1, spacer, col2 = st.columns([0.05, 2, 0.05, 1])
    with col1:

        st.markdown("#### What it does", unsafe_allow_html=True)
        st.markdown(" &nbsp; • &nbsp; &nbsp; Analyses a target URL and proposes the best elements to scrape.\n\n")
        st.markdown(" &nbsp; • &nbsp; &nbsp; Generates production-ready FastAPI code and Markdown docs.\n\n")
        st.markdown(" &nbsp; • &nbsp; &nbsp; Lets you preview live data and export JSON / CSV.\n\n")
        st.markdown(" &nbsp; • &nbsp; &nbsp; Can merge the new API into an existing Python project.\n\n\n")
        

        st.markdown("#### Quick workflow", unsafe_allow_html=True)
        st.markdown(
            "1. **Paste URL + goal**  \n  2. **Pick fields**   \n "
            "3. **Generate API**  \n  4. **Download or merge**\n"
        )

    
    with col2:
    
        st.markdown("<h4>Quick Start</h4>", unsafe_allow_html=True)
        st.write("Ready to create your API? Click below to get started!")
        if st.button("Start Extracting Data", key="start_button"):
            st.session_state.page = "Extract"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
    
        

# Extract page
def ask_gpt_for_data_fields(url, user_explanation, html_content):
    prompt = f"""
You are an expert web scraping assistant. The user wants to extract data from the website at URL: {url}
The filtered HTML content of the page will be provided below:

----------------
They have described their data needs as: "{user_explanation}".

Your task is to analyse the HTML and return a structured JSON object 
that identifies the best elements to scrape based on the user’s intent.

Return a JSON object with two arrays:

- "recommended_fields": The most relevant fields the user likely wants (3–5 items)
- "other_interesting_fields": Additional useful fields present in the page (3–8 items)

Each field object must include:
- "field": A short, consistent identifier (e.g., "product_title")
- "explanation": A short description of what the field contains
- "tag": A **single comma-separated string** of 2–5 CSS selectors that exactly match the element(s)
  - Include both item-level and list/grid-level selectors if applicable
  - Use schema.org attributes when present (e.g., [itemprop='price'])
  - provide the 

Very important: The selectors must be copy-paste ready for frameworks like BeautifulSoup, Puppeteer, or Playwright.

Output must be **valid JSON only**, with no additional explanation or commentary.
Do not wrap the JSON in triple backticks or any code block.
Return only valid JSON starting at the first character.

----------------
HTML content:
{html_content}

"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        content = response["choices"][0]["message"]["content"].strip()
        print("📦 GPT Raw Response:")
        print(content)
        return content
    except Exception as e:
        print(f"Error calling OpenAI API: {str(e)}")
        return json.dumps({
            "error": f"Failed to get field recommendations: {str(e)}",
            "recommended_fields": [],
            "other_interesting_fields": []
        })

def extract_page():
    st.markdown("<h1 class='header-text'>Extract Data Fields</h1>", unsafe_allow_html=True)
    
    st.write("Enter the website URL and describe what data you want to extract.")
    
    # Check if API key is already set
    has_api_key = set_openai_key()
    
    if not has_api_key:
        st.error("OpenAI API key not found in .env file. Please make sure it's properly configured.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        url = st.text_input("Website URL:", placeholder="https://example.com")
    
    with col2:
        user_explanation = st.text_area(
            "Describe what data you want to extract:",
            placeholder="Example: I want to extract product titles and prices from this e-commerce page."
        )
    
    if st.button("Analyse the website", disabled=not has_api_key) and url and user_explanation:
        with st.spinner("Analyzing your request and fetching essential HTML..."):
            try:
                # Fetch the full HTML
                response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
                response.raise_for_status()
                full_html = response.text

                # Parse HTML and remove unessential elements
                soup = BeautifulSoup(full_html, 'html.parser')

                # Remove common non-essential tags (including img if desired)
                for tag in soup([
                    "script", "style", "header", "footer", "nav", "aside", "noscript", 
                    "iframe", "svg", "object", "embed", "img", "canvas", "video", "audio"
                ]):
                    tag.decompose()

                # Remove comments
                for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                    comment.extract()

                # Focus on <main> if available; otherwise use <body>
                if soup.main:
                    essential_html = soup.main.decode_contents()
                elif soup.body:
                    essential_html = soup.body.decode_contents()
                else:
                    essential_html = full_html  # fallback
                    
                # Cut HTML to first 500,000 characters to stay under token limits
                MAX_HTML_CHARS = 420000
                if len(essential_html) > MAX_HTML_CHARS:
                    essential_html = essential_html[:MAX_HTML_CHARS]

                if len(essential_html) > MAX_HTML_CHARS:
                    st.warning(f"HTML content was trimmed to {MAX_HTML_CHARS:,} characters to stay within GPT limits.")
                    essential_html = essential_html[:MAX_HTML_CHARS]
                
                
                print(f"📏 HTML character length: {len(essential_html)}")

                # Now, call GPT with the filtered HTML content
                gpt_response = ask_gpt_for_data_fields(url, user_explanation, essential_html)
                
                # See GPT output:
                #st.markdown("### Raw GPT Response")
                #st.code(gpt_response, language="json")
                
                try:
                    guessed_fields_obj = json.loads(gpt_response)
                except Exception as json_err:
                    st.error("Error parsing GPT response as JSON: " + str(json_err))
                    guessed_fields_obj = {}

                st.session_state["guessed_fields"] = guessed_fields_obj
                st.session_state["url"] = url

                # Estimate token usage based on the filtered HTML content
                char_count = len(essential_html)
                estimated_tokens = char_count / 4  # using 4 characters per token as an average heuristic
                estimated_cost = (estimated_tokens / 1000) * 0.005  # GPT-4o input cost

                # Display filtered HTML
                # with st.expander("📄 Essential HTML Content (optional view)", expanded=False):
                #     st.text_area("Essential HTML", essential_html, height=300)

                st.success("Analysis and HTML fetch complete.")

            except Exception as e:
                st.error(f"Failed to analyse with AI or fetch HTML: {e}")




    st.markdown("</div>", unsafe_allow_html=True)
    
    # Only show the rest of the UI if GPT has been queried
    if "guessed_fields" in st.session_state and "url" in st.session_state:
        url = st.session_state["url"]
        
        try:
            # Fetch and parse the website HTML
            with st.spinner("Fetching website content..."):
                response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                st.session_state["soup"] = soup
                
            col1, col2 = st.columns(2)
            
            # Recommended Fields Section
            with col1:
            
                st.subheader("Recommended Fields")
                st.write("These are the main fields based on your description.")
                
                for idx, field_obj in enumerate(st.session_state["guessed_fields"].get("recommended_fields", [])):
                    field_name = field_obj.get("field")
                    explanation = field_obj.get("explanation")
                    tag = field_obj.get("tag")
                    
                    st.checkbox(
                        f"{field_name}",
                        value=True,
                        key=f"rec_field_{idx}",
                        help=f"{explanation} (Tag: {tag})"
                    )
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Other Interesting Fields Section
            with col2:
            
                st.subheader("Other Interesting Fields")
                st.write("These additional fields might also be useful.")
                
                for idx, field_obj in enumerate(st.session_state["guessed_fields"].get("other_interesting_fields", [])):
                    field_name = field_obj.get("field")
                    explanation = field_obj.get("explanation")
                    tag = field_obj.get("tag")
                    
                    st.checkbox(
                        f"{field_name}",
                        key=f"other_field_{idx}",
                        help=f"{explanation} (Tag: {tag})"
                    )
                
                st.markdown("</div>", unsafe_allow_html=True)
            

            st.write("Select your desired fields and click the button below to generate your API.")

            if st.button("Generate API & Documentation", key="generate_button"):
                # Collect selected fields (both recommended and other)
                selected_fields = []
                
                # Check recommended fields
                for idx, field_obj in enumerate(st.session_state["guessed_fields"].get("recommended_fields", [])):
                    # If the checkbox is checked (default was True)
                    if st.session_state.get(f"rec_field_{idx}", False):
                        selected_fields.append(field_obj)
                
                # Check other fields
                for idx, field_obj in enumerate(st.session_state["guessed_fields"].get("other_interesting_fields", [])):
                    if st.session_state.get(f"other_field_{idx}", False):
                        selected_fields.append(field_obj)
                
                # Ensure that at least one field is selected
                if not selected_fields:
                    st.error("Please select at least one field before generating the API.")
                else:
                    st.session_state["selected_fields"] = selected_fields
                    st.session_state["page"] = "Results"
                    st.rerun()

            
            st.markdown("</div>", unsafe_allow_html=True)
        
        except Exception as e:
            st.error(f"Error fetching or parsing the website: {e}")

# Results page
def generate_api_code(url, selected_fields):
    """Generate a more robust FastAPI endpoint based on the selected fields and their recommended tags."""
    fields_json = json.dumps(selected_fields, indent=4)
    
    return f"""
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import re
from typing import Dict, List, Any, Optional
import time
from datetime import datetime
import asyncio
import logging
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("web_scraper_api")

app = FastAPI(
    title="Web Scraper API",
    description="API for extracting data from {url}",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache for storing recently scraped data
data_cache = {{}}
CACHE_TIMEOUT = 3600  # Cache timeout in seconds (1 hour)

# Define the fields to extract
SELECTED_FIELDS = {fields_json}

class ScrapingStatus(BaseModel):
    task_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    message: Optional[str] = None

# Store for background tasks
background_tasks = {{}}

# Helper functions
def generate_alternative_selectors(original_selector):
    alternatives = []
    
    # Remove the last part of the selector (make it more general)
    parts = original_selector.split('>')
    if len(parts) > 1:
        alternatives.append('>'.join(parts[:-1]).strip())
    
    # Try with just the tag name if there's a class
    if '.' in original_selector:
        tag = original_selector.split('.')[0]
        if tag:
            alternatives.append(tag)
    
    # Try with just the class name
    class_match = re.search(r'\.([a-zA-Z0-9_-]+)', original_selector)
    if class_match:
        alternatives.append(f".{{class_match.group(1)}}")
    
    return alternatives

def extract_data_from_website(url="{url}"):
    try:
        # Check cache first
        cache_key = f"{{url}}_data"
        if cache_key in data_cache:
            cache_entry = data_cache[cache_key]
            if time.time() - cache_entry["timestamp"] < CACHE_TIMEOUT:
                logger.info(f"Returning cached data for {{url}}")
                return cache_entry["data"]
        
        # Fetch the website content with a user agent
        headers = {{
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }}
        logger.info(f"Fetching website content from {{url}}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = {{}}
        for field_obj in SELECTED_FIELDS:
            field_name = field_obj.get("field")
            css_selector = field_obj.get("tag")
            
            if not css_selector:
                continue
                
            # Try each selector (they might be comma-separated)
            all_elements = []
            for selector in css_selector.split(','):
                selector = selector.strip()
                elements = soup.select(selector)
                if elements:
                    all_elements.extend(elements)
                    break  # If we found elements, no need to try other selectors
            
            # If no elements found, try alternative selectors
            if not all_elements:
                for selector in css_selector.split(','):
                    selector = selector.strip()
                    alternatives = generate_alternative_selectors(selector)
                    for alt_selector in alternatives:
                        elements = soup.select(alt_selector)
                        if elements:
                            all_elements.extend(elements)
                            break
                    if all_elements:
                        break
            
            # Extract text and clean it
            results[field_name] = []
            for elem in all_elements:
                text = elem.get_text().strip()
                # Remove excessive whitespace
                text = re.sub(r'\\s+', ' ', text)
                results[field_name].append(text)
        
        # Cache the results
        data_cache[cache_key] = {{
            "timestamp": time.time(),
            "data": results
        }}
        
        return results
    except Exception as e:
        logger.error(f"Error extracting data: {{str(e)}}")
        raise HTTPException(status_code=500, detail=f"Error extracting data: {{str(e)}}")

async def background_scrape(task_id: str, url: str):
    try:
        background_tasks[task_id].status = "in_progress"
        data = extract_data_from_website(url)
        background_tasks[task_id].status = "completed"
        background_tasks[task_id].completed_at = datetime.now()
        background_tasks[task_id].message = "Data extraction completed successfully"
        # Cache the results with the task ID
        data_cache[task_id] = {{
            "timestamp": time.time(),
            "data": data
        }}
    except Exception as e:
        background_tasks[task_id].status = "failed"
        background_tasks[task_id].completed_at = datetime.now()
        background_tasks[task_id].message = f"Error: {{str(e)}}"

@app.get("/")
async def root():
    return {{"message": "Welcome to the Web Scraper API", "endpoints": [
        "/api/extract", 
        "/api/extract/csv",
        "/api/extract/async",
        "/api/status/{{task_id}}",
        "/api/fields"
    ]}}

@app.get("/api/fields")
async def get_fields():
    return {{"fields": SELECTED_FIELDS}}

@app.get("/api/extract")
async def extract_data(refresh: bool = Query(False, description="Force refresh cached data")):
    cache_key = f"{url}_data"
    if not refresh and cache_key in data_cache:
        cache_entry = data_cache[cache_key]
        if time.time() - cache_entry["timestamp"] < CACHE_TIMEOUT:
            return cache_entry["data"]
    
    return extract_data_from_website()

@app.get("/api/extract/csv")
async def extract_data_csv(refresh: bool = Query(False, description="Force refresh cached data")):
    try:
        # Get the data (using cache if available)
        data = await extract_data(refresh=refresh)
        
        # Convert to DataFrame
        # Handle different length arrays by padding with None
        max_length = max([len(v) for v in data.values()]) if data else 0
        padded_data = {{}}
        
        for k, v in data.items():
            padded_data[k] = v + [None] * (max_length - len(v))
            
        df = pd.DataFrame(padded_data)
        csv_string = df.to_csv(index=False)
        
        # Return as downloadable CSV
        headers = {{
            "Content-Disposition": "attachment; filename=extracted_data.csv"
        }}
        return JSONResponse(content={{"csv": csv_string}}, headers=headers)
    except Exception as e:
        logger.error(f"Error generating CSV: {{str(e)}}")
        raise HTTPException(status_code=500, detail=f"Error generating CSV: {{str(e)}}")

@app.get("/api/extract/async")
async def extract_data_async(background_tasks: BackgroundTasks):
    task_id = f"task_{{int(time.time())}}"
    
    # Create a new task status object
    task_status = ScrapingStatus(
        task_id=task_id,
        status="pending",
        started_at=datetime.now()
    )
    
    # Store the task status
    background_tasks[task_id] = task_status
    
    # Start the background task
    background_tasks.add_task(background_scrape, task_id, "{url}")
    
    return {{"task_id": task_id, "status": "pending", "message": "Data extraction started"}}

@app.get("/api/status/{{task_id}}")
async def get_task_status(task_id: str):
    if task_id not in background_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = background_tasks[task_id]
    
    if task.status == "completed" and task_id in data_cache:
        # Include the data in the response
        return {{
            "status": task.status,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "message": task.message,
            "data": data_cache[task_id]["data"]
        }}
    
    return {{
        "status": task.status,
        "started_at": task.started_at,
        "completed_at": task.completed_at,
        "message": task.message
    }}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""

def generate_documentation(url, selected_fields):
    """Generate Markdown documentation for the API based on selected fields."""
    fields_str = "\n".join(
        f"- **{f['field']}**: {f['explanation']} (Tag: `{f.get('tag', 'N/A')}`)" 
        for f in selected_fields
    )
    
    return f"""
# Web Scraper API Documentation

## Overview

This API extracts data from [{url}]({url}) using BeautifulSoup and FastAPI. It provides endpoints for retrieving the extracted data in both JSON and CSV formats.

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install fastapi uvicorn requests beautifulsoup4 pandas
   ```
3. Run the server:
   ```
   uvicorn main:app --reload
   ```

## Endpoints

### GET /

Returns a welcome message and available endpoints.

### GET /api/extract

Returns data extracted from the website using the configured CSS selectors in JSON format.

### GET /api/extract/csv

Returns the same data as `/api/extract` but formatted as a CSV file for download.

## Data Fields

The following data fields are extracted from the target website:

{fields_str}

## Response Format

### JSON Response

```json
{{
  "field_name": ["extracted text", ...],
  ...
}}
```

### CSV Response

The CSV endpoint returns a JSON object with a `csv` key containing a string representation of the CSV data.

## Error Handling

If the scraping process fails, the API will return a 500 error with details about what went wrong.

## Usage Considerations

- This API scrapes data in real-time, so it's dependent on the target website's availability
- If the target website changes its structure, the selectors may need to be updated
- Be respectful of the target website's terms of service and avoid excessive requests
- Consider implementing caching to reduce load on the target website

## License

MIT
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

def extract_data_from_website(url, selected_fields):
    """
    Extract data from a website using requests and BeautifulSoup.
    Falls back to Selenium if simple request doesn't work.
    """
    try:
        # First attempt with simple requests
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        response.raise_for_status()
        html = response.text
        
        # Try parsing with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check if we got meaningful content (many sites block simple requests)
        if len(soup.text.strip()) < 100:  # Too little content usually means blocking
            raise Exception("Website might be blocking simple requests")
            
        # Extract data using the selected fields
        results = {}
        for field_obj in selected_fields:
            field_name = field_obj.get("field")
            css_selector = field_obj.get("tag")
            
            if not css_selector:
                continue
                
            elements = soup.select(css_selector)
            if not elements:
                # Try alternative selectors if the original one doesn't work
                alt_selectors = generate_alternative_selectors(css_selector)
                for alt_selector in alt_selectors:
                    elements = soup.select(alt_selector)
                    if elements:
                        break
            
            # Extract the text from each element
            results[field_name] = [elem.text.strip() for elem in elements]
            
            # If no results and the field is important, try JavaScript attributes
            if not results[field_name]:
                # Look for data in JavaScript or JSON embedded in the page
                js_data = extract_from_javascript(soup, field_name)
                if js_data:
                    results[field_name] = js_data
        
        return results
        
    except Exception as e:
        # Log the exception for debugging
        print(f"Error with simple extraction: {str(e)}")
        
        # Fall back to Selenium for JavaScript-heavy sites
        print("Falling back to Selenium for extraction...")
        try:
            # Set up Chrome options for headless browsing
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            # Initialize the driver
            driver = webdriver.Chrome(options=chrome_options)
            
            # Set page load timeout
            driver.set_page_load_timeout(30)
            
            try:
                # Navigate to the URL
                driver.get(url)
                
                # Wait for page to load (you can adjust the wait time)
                import time
                time.sleep(3)  # Simple wait
                
                # Get page source and parse with BeautifulSoup
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract data using the selected fields
                results = {}
                for field_obj in selected_fields:
                    field_name = field_obj.get("field")
                    css_selector = field_obj.get("tag")
                    
                    if not css_selector:
                        continue
                    
                    # Try each selector (they might be comma-separated)
                    elements = []
                    for selector in css_selector.split(','):
                        selector = selector.strip()
                        try:
                            # Try with Selenium first for dynamic content
                            selenium_elements = driver.find_elements_by_css_selector(selector)
                            if selenium_elements:
                                elements = selenium_elements
                                break
                        except Exception:
                            # If Selenium selector fails, try with BeautifulSoup
                            bs_elements = soup.select(selector)
                            if bs_elements:
                                elements = bs_elements
                                break
                    
                    # If no elements found, try alternative selectors
                    if not elements:
                        for selector in css_selector.split(','):
                            selector = selector.strip()
                            alternatives = generate_alternative_selectors(selector)
                            for alt_selector in alternatives:
                                try:
                                    # Try with Selenium first
                                    selenium_elements = driver.find_elements_by_css_selector(alt_selector)
                                    if selenium_elements:
                                        elements = selenium_elements
                                        break
                                except Exception:
                                    # Fall back to BeautifulSoup
                                    bs_elements = soup.select(alt_selector)
                                    if bs_elements:
                                        elements = bs_elements
                                        break
                            if elements:
                                break
                    
                    # Extract text from elements
                    results[field_name] = []
                    
                    # Handle different element types (Selenium vs BeautifulSoup)
                    for elem in elements:
                        if hasattr(elem, 'text'):  # BeautifulSoup element
                            text = elem.text.strip()
                        else:  # Selenium WebElement
                            text = elem.text.strip()
                        
                        # Remove excessive whitespace
                        text = re.sub(r'\s+', ' ', text)
                        results[field_name].append(text)
                
                return results
                
            finally:
                # Always close the driver to free resources
                driver.quit()
                
        except Exception as selenium_e:
            print(f"Selenium extraction also failed: {str(selenium_e)}")
            
            # Last resort: try with a different requests parser
            try:
                response = requests.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                soup = BeautifulSoup(response.text, 'html5lib')  # Use html5lib if available
                
                results = {}
                for field_obj in selected_fields:
                    field_name = field_obj.get("field")
                    css_selector = field_obj.get("tag")
                    
                    if not css_selector:
                        continue
                        
                    # Try with more flexible selector
                    elements = soup.select(css_selector)
                    results[field_name] = [elem.text.strip() for elem in elements]
                    
                return results
            except Exception as final_e:
                return {"error": f"All extraction methods failed. Last error: {str(final_e)}"}
            
def generate_alternative_selectors(original_selector):
    """Generate alternative selectors if the original one doesn't work."""
    alternatives = []
    
    # Remove the last part of the selector (make it more general)
    parts = original_selector.split('>')
    if len(parts) > 1:
        alternatives.append('>'.join(parts[:-1]).strip())
    
    # Try with just the tag name if there's a class
    if '.' in original_selector:
        tag = original_selector.split('.')[0]
        if tag:
            alternatives.append(tag)
    
    # Try with just the class name
    class_match = re.search(r'\.([a-zA-Z0-9_-]+)', original_selector)
    if class_match:
        alternatives.append(f".{class_match.group(1)}")
    
    # Try with just the ID if there is one
    id_match = re.search(r'#([a-zA-Z0-9_-]+)', original_selector)
    if id_match:
        alternatives.append(f"#{id_match.group(1)}")
    
    return alternatives

def extract_from_javascript(soup, field_name):
    """Try to extract data from JavaScript/JSON blocks in the page."""
    # Look for script tags that might contain our data
    scripts = soup.find_all('script')
    
    search_patterns = [
        rf'"{field_name}"\s*:\s*(\[[^\]]+\])',  # JSON array
        rf'"{field_name}"\s*:\s*"([^"]+)"',     # JSON string value
        rf'var\s+{field_name}\s*=\s*\[([^\]]+)\]',  # JS array
        rf'let\s+{field_name}\s*=\s*\[([^\]]+)\]',  # JS array with let
        rf'const\s+{field_name}\s*=\s*\[([^\]]+)\]'  # JS array with const
    ]
    
    for script in scripts:
        if script.string:
            for pattern in search_patterns:
                matches = re.search(pattern, script.string)
                if matches:
                    # If we found a match, try to parse it
                    try:
                        data = matches.group(1)
                        if data.startswith('[') and data.endswith(']'):
                            # It's a JSON array
                            return json.loads(data)
                        else:
                            # It's probably a comma-separated list
                            return [item.strip(' "\'') for item in data.split(',')]
                    except:
                        continue
    
    return []

def create_download_link(data, filename, link_text):
    """Create a download link for a file."""
    b64 = base64.b64encode(data.encode()).decode()
    href = f'data:file/txt;base64,{b64}'
    return f'<a href="{href}" download="{filename}">{link_text}</a>'

def results_page():
    st.markdown("<h1 class='header-text'>Generated API</h1>", unsafe_allow_html=True)
    
    # Check if we have the necessary data
    if "selected_fields" not in st.session_state or "url" not in st.session_state:
        st.warning("Please go back to the Extract page and select fields first.")
        if st.button("Go to Extract Page"):
            st.session_state.page = "Extract"
            st.rerun()
        return
    
    url = st.session_state["url"]
    selected_fields = st.session_state["selected_fields"]
    
    # Generate code and documentation
    api_code = generate_api_code(url, selected_fields)
    docs = generate_documentation(url, selected_fields)
    
    # Save to session state
    st.session_state["api_code"] = api_code
    st.session_state["docs"] = docs
    
    # Display tabs
    tab1, tab2, tab3 = st.tabs(["API Code", "Documentation", "Test & Export"])
    
    with tab1:
    
        st.subheader("Generated FastAPI Code")
        st.code(api_code, language="python")
        
        st.download_button(
            label="Download API Code",
            data=api_code,
            file_name="web_scraper_api.py",
            mime="text/plain"
        )
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab2:
    
        st.subheader("API Documentation")
        st.markdown(docs)
        
        st.download_button(
            label="Download Documentation",
            data=docs,
            file_name="README.md",
            mime="text/plain"
        )
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab3:

        st.subheader("Test Extraction")

        if st.button("Extract Data Now", key="extract_now"):
            with st.spinner("Fetching data from website..."):
                extracted_data = extract_data_from_website(url, selected_fields)
                st.session_state["extracted_data"] = extracted_data

        if "extracted_data" in st.session_state:
            data = st.session_state["extracted_data"]

            if "error" in data:
                st.error(f"Error extracting data: {data['error']}")
            else:
                st.success("Data extracted successfully!")

                # show JSON preview 
                st.markdown("##### JSON preview")
                st.json(data, expanded=False)  
                st.markdown("---")

                # Convert to DataFrame for display
                # Handle different array lengths
                max_length = max(len(v) for v in data.values()) if data else 0
                padded_data = {
                    k: v + [None] * (max_length - len(v))
                    for k, v in data.items()
                }
                df = pd.DataFrame(padded_data)

                st.markdown("##### Table view")
                st.dataframe(df, use_container_width=True)

                # Download options
                col1, col2 = st.columns(2)

                with col1:
                    # JSON download
                    json_data = json.dumps(data, indent=4)
                    st.download_button(
                        label="Download as JSON",
                        data=json_data,
                        file_name="extracted_data.json",
                        mime="application/json"
                    )

                with col2:
                    # CSV download
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download as CSV",
                        data=csv,
                        file_name="extracted_data.csv",
                        mime="text/csv"
                    )

        st.markdown("</div>", unsafe_allow_html=True)


# Merge code page
def merge_code_page():
    st.markdown("<h1 class='header-text'>Merge with Existing Code</h1>", unsafe_allow_html=True)
    

    st.write("""
    This feature allows you to merge the generated API with your existing code. 
    Paste your code below (maximum 200 lines) and we'll use AI to integrate the generated API functionality.
    """)
    
    # Check if we have the necessary data
    if "api_code" not in st.session_state:
        st.warning("Please generate an API first before attempting to merge.")
        return
    
    # Check if API key is set
    has_api_key = set_openai_key()
    if not has_api_key:
        st.error("OpenAI API key not found in .env file. Please make sure it's properly configured.")
        return
    
    user_code = st.text_area("Paste your existing code here (max 200 lines):", height=300)
    
    if st.button("Merge Code") and user_code:
        # Validate input
        code_lines = user_code.strip().split("\n")
        if len(code_lines) > 200:
            st.error("Code exceeds 200 lines limit. Please reduce the size.")
            return
        
        with st.spinner("Merging code with AI..."):
            try:
                api_code = st.session_state["api_code"]
                prompt = f"""
                I have two Python code snippets that I want to merge:
                
                1. EXISTING CODE:
                ```python
                {user_code}
                ```
                
                2. API CODE TO INTEGRATE:
                ```python
                {api_code}
                ```
                
                Please merge these two codebases intelligently, with these guidelines:
                - Keep all the functionalities of both codes
                - Resolve any import duplications
                - Maintain the FastAPI functionality from the second snippet
                - Ensure the merged code is clean, well-structured, and follows best practices, and ready for production release
                - Add appropriate comments to explain the integration
                - Make sure the final code is runnable
                
                Return ONLY the merged code without any explanations or markdown.
                """
                
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=4000
                )
                
                merged_code = response["choices"][0]["message"]["content"].strip()
                
                # Clean up possible markdown code blocks
                merged_code = re.sub(r'^```python\s*', '', merged_code)
                merged_code = re.sub(r'```\s*$', '', merged_code)
                
                st.session_state["merged_code"] = merged_code
                st.success("Code merged successfully!")
                
            except Exception as e:
                st.error(f"Failed to merge code: {e}")
    
    if "merged_code" in st.session_state:
        st.subheader("Merged Code")
        st.code(st.session_state["merged_code"], language="python")
        
        st.download_button(
            label="Download Merged Code",
            data=st.session_state["merged_code"],
            file_name="merged_web_scraper.py",
            mime="text/plain"
        )
    
    st.markdown("</div>", unsafe_allow_html=True)

# Main app
def main():
    # Initialize session state
    if "page" not in st.session_state:
        st.session_state.page = "Home"
    
    # Handle navigation
    selected = navigation()
    if selected != st.session_state.page:
        st.session_state.page = selected
        st.rerun()
    
    # Display the selected page
    if st.session_state.page == "Home":
        home_page()
    elif st.session_state.page == "Extract":
        extract_page()
    elif st.session_state.page == "Results":
        results_page()
    elif st.session_state.page == "Merge Code":
        merge_code_page()

if __name__ == "__main__":
    main()
