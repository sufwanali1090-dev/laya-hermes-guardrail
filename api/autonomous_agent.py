import time
import json
from http.server import BaseHTTPRequestHandler
from google import genai
from google.genai import types
import os

# Initialize client using environment variable
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Define a primary and backup model
PRIMARY_MODEL = "gemini-3.8-flash"
BACKUP_MODEL = "gemini-3.6-flash"

def ask_gemini_with_retry(prompt, max_retries=3):
    models_to_try = [PRIMARY_MODEL, BACKUP_MODEL]
    
    for attempt in range(max_retries):
        for model in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                )
                return response.text, model
                
            except Exception as e:
                err_str = str(e)
                # If it's a 503 High Demand error, wait and retry
                if "503" in err_str or "UNAVAILABLE" in err_str:
                    wait_time = (2 ** attempt) # Exponential backoff: waits 1s, then 2s, then 4s
                    print(f"Model {model} overloaded (503). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    # If it's a different error (like 401 unauthorized), raise it immediately
                    raise e
                    
    raise Exception("Both Primary and Backup Gemini models are currently overloaded. Agent standing by.")

class handler(BaseHTTPRequestHandler):
    # ... keep your existing do_GET method here ...

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            req_data = json.loads(post_data.decode('utf-8'))
            user_prompt = req_data.get('prompt', '')
            
            # Use the new resilient retry function
            agent_response, used_model = ask_gemini_with_retry(user_prompt)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            payload = {
                "agent_status": "SUCCESS",
                "model_used": used_model,
                "agent_response": agent_response
            }
            self.wfile.write(json.dumps(payload).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
