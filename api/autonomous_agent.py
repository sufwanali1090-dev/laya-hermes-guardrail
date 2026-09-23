from http.server import BaseHTTPRequestHandler
import json
import os
from google import genai
from google.genai import types

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Handle direct browser visits gracefully
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response_data = {"status": "online", "message": "Laya Autonomous Agent endpoint is active. Send a POST request with a prompt."}
        self.wfile.write(json.dumps(response_data).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            req_data = json.loads(post_data.decode('utf-8')) if post_data else {}
            user_directive = req_data.get('prompt', 'Analyze current Polygon DeFi market conditions and formulate high-yield triangular arbitrage paths.')
            
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable not configured in Vercel.")
                
            client = genai.Client(api_key=api_key)
            model_id = "gemini-3.8-flash" 
# You can also use "gemini-3.6-flash" as the error suggested
            
            system_instruction = (
                "You are an elite autonomous DeFi and arbitrage strategy agent operating on Polygon PoS (Chain ID 137). "
                "You have full reasoning capabilities, internet access, and freedom to analyze market metrics, "
                "propose triangular swap paths, and evaluate risk parameters. Never suggest routes touching blacklisted or toxic pools."
            )
            
            response = client.models.generate_content(
                model=model_id,
                contents=user_directive,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                    max_output_tokens=1000,
                ),
            )
            
            response_payload = {
                "agent_status": "SUCCESS",
                "model_used": model_id,
                "directive": user_directive,
                "agent_response": response.text,
                "action": "DISPATCH_TO_LAYA_GUARDRAIL"
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_payload).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
