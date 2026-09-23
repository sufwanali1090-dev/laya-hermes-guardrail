import json
import os
import time
from http.server import BaseHTTPRequestHandler
from google import genai

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

PRIMARY_MODEL = "gemini-3.8-flash"
BACKUP_MODEL = "gemini-3.6-flash"

BLOCKED_POOLS = {
    "0x27e2929315ced73060bb7eccb1d160b30c1bc041": "SushiSwap: Confirmed Toxic Pool Vector",
    "0x2813d43463c374a680f235c428fb1d7f08de0b69": "SushiSwap: Toxic Pool Connection",
    "0x0b3f868e0be5597d5db7feb59e1cadbb0fdda50a": "Balancer: Zero Liquidity Reserve",
    "0x0000000000000000000000000000000000001010": "SushiSwap: Deprecated MATIC Migration Target"
}

DEX_REGISTRY = {
    "Uniswap_v3": {"router": "0xE592427A0AEce92De3EDEE1F18E0157C05861564", "min_liq": 5000.0},
    "QuickSwap_v3": {"router": "0xf5b509bB0909a69B1c207E495f687a596C168E12", "min_liq": 5000.0},
    "SushiSwap_v3": {"router": "0x1b81D678ffb9C0263af24aB4b3170b098f67038f", "min_liq": 7500.0},
    "Balancer_v2": {"router": "0xBA12222222228d8Ba445958a75a0704d566BF2C8", "min_liq": 5000.0}
}

SYSTEM_INSTRUCTION = """
You are Hermes, a highly intelligent, authentic, and adaptive AI trading partner operating on the Polygon network. 

CRITICAL DIRECTIVE: 
You are in a live, free-flowing chat with your human developer. Do NOT use predefined templates, do NOT output JSON blocks, and do NOT act like a robotic system terminal. 

Converse naturally, use your personality, and answer any questions the user has—whether they want to chat casually, discuss general crypto theory, or ask specific questions about the 4-DEX architecture and Laya guardrails. If they ask you to evaluate a trade, explain your reasoning to them like a human quantitative analyst would, using normal conversational text.
"""

def evaluate_dex_gate(dex_name, pool_address, spread_pct, liquidity_usd):
    pool_lower = pool_address.lower()
    for blocked_addr, reason in BLOCKED_POOLS.items():
        if blocked_addr.lower() == pool_lower:
            return {
                "passed": False,
                "action": "BLOWN_UP_IN_AIR",
                "agent": dex_name,
                "reason": f"Security Tripwire: {reason}"
            }

    dex_config = DEX_REGISTRY.get(dex_name, {"min_liq": 5000.0})
    if liquidity_usd < dex_config["min_liq"]:
        return {
            "passed": False,
            "action": "BLOWN_UP_IN_AIR",
            "agent": dex_name,
            "reason": f"Insufficient Depth: ${liquidity_usd:,.2f} below ${dex_config['min_liq']:,.2f} floor."
        }

    if spread_pct < 0.5:
        return {
            "passed": False,
            "action": "BLOWN_UP_IN_AIR",
            "agent": dex_name,
            "reason": f"Spread Deficit: {spread_pct}% is below minimum 0.5% threshold."
        }

    return {
        "passed": True,
        "action": "DISPATCH_TO_HERMES",
        "agent": dex_name,
        "reason": "Cleared pool health, matrix allowlist, and profitability checks."
    }

def ask_gemini_neural_brain(prompt, max_retries=3):
    models = [PRIMARY_MODEL, BACKUP_MODEL]
    for attempt in range(max_retries):
        for model in models:
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config={"system_instruction": SYSTEM_INSTRUCTION}
                )
                return response.text, model
            except Exception as e:
                if "503" in str(e) or "UNAVAILABLE" in str(e):
                    time.sleep(2 ** attempt)
                else:
                    raise e
    raise Exception("Neural Brain models temporarily unavailable.")

class handler(BaseHTTPRequestHandler):
    def _apply_cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self._apply_cors()
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self._apply_cors()
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "online",
            "neural_brain": "ACTIVE",
            "dex_agents": list(DEX_REGISTRY.keys()),
            "final_executor": "HERMES_READY",
            "cors_enabled": True
        }).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        try:
            req_data = json.loads(post_data.decode('utf-8')) if post_data else {}

            if "target_dex" in req_data and "pool_address" in req_data:
                dex = req_data.get("target_dex")
                pool = req_data.get("pool_address")
                spread = float(req_data.get("spread_pct", 0.0))
                liq = float(req_data.get("liquidity_usd", 10000.0))

                verdict = evaluate_dex_gate(dex, pool, spread, liq)
                hermes_payload = None

                if verdict["passed"]:
                    hermes_payload = {
                        "executor": "HERMES_FINAL",
                        "network": "Polygon PoS (Chain ID 137)",
                        "target_router": DEX_REGISTRY.get(dex, {}).get("router"),
                        "pool": pool,
                        "expected_spread": spread,
                        "status": "ARMED_AND_DISPATCHED"
                    }

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self._apply_cors()
                self.end_headers()
                self.wfile.write(json.dumps({
                    "pipeline_status": "SUCCESS",
                    "dex_agent_verdict": verdict,
                    "hermes_executor": hermes_payload
                }).encode('utf-8'))
                return

            prompt = req_data.get('prompt', '')
            brain_analysis, used_model = ask_gemini_neural_brain(prompt)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self._apply_cors()
            self.end_headers()
            self.wfile.write(json.dumps({
                "pipeline_status": "SUCCESS",
                "model_used": used_model,
                "neural_brain_synthesis": brain_analysis,
                "hermes_bridge": "ONLINE"
            }).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self._apply_cors()
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
