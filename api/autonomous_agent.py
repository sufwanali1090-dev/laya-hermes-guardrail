from http.server import BaseHTTPRequestHandler
import json
import os
from google import genai
from google.genai import types

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            req_data = json.loads(post_data.decode('utf-8'))
            user_directive = req_data.get('prompt', 'Analyze current Polygon DeFi market conditions and formulate high-yield triangular arbitrage paths.')
            
            # Initialize the Gemini GenAI client using Google AI Studio API key stored in Vercel environment variables
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable not configured in Vercel.")
                
            client = genai.Client(api_key=api_key)
            
            # Use Gemini 3.1 Pro - Google's highest-tier reasoning model for deep analytical tasks
            model_id = "gemini-3.1-pro-preview"
            
            # Construct the system instruction and prompt for the autonomous agent
            system_instruction = (
                "You are an elite autonomous DeFi and arbitrage strategy agent operating on Polygon PoS (Chain ID 137). "
                "You have full reasoning capabilities, internet access, and freedom to analyze market metrics, "
                "propose triangular swap paths, and evaluate risk parameters (such as USD liquidity floors and slippage limits). "
                "Never suggest routes touching blacklisted or toxic pools."
            )
            
            response = client.models.generate_content(
                model=model_id,
                contents=user_directive,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2, # Low temperature for precise, deterministic mathematical/financial reasoning
                    max_output_tokens=1000,
                ),
            )
            
            # Format the output for your frontend terminal and Laya guardrail
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
