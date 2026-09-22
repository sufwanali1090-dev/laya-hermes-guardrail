from http.server import BaseHTTPRequestHandler
import json

# Official Allowlist Registry
POLYGON_TOKENS = {
    "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
    "USDC": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
    "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
    "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
    "WPOL": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"
}

BLACKLISTED_POOLS = {
    "0x27e2929315ced73060bb7eccb1d160b30c1bc041", # Toxic Sushi Pool (Historical loss vector)
    "0x2813d43463c374a680f235c428fb1d7f08de0b69"
}

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            chain_id = data.get('chain_id', 137)
            pool_address = data.get('pool_address', '').lower()
            base_token = data.get('base_token')
            quote_token = data.get('quote_token')
            spread_pct = float(data.get('spread_pct', 0.0))
            pool_liquidity_usd = float(data.get('pool_liquidity_usd', 10000.0))
            
            # --- Laya Decision Matrix Evaluation ---
            
            # 1. Chain Verification
            if chain_id != 137:
                self._send_json(200, {"decision": "REJECT", "reason": "Non-Polygon chain ID detected."})
                return

            # 2. Toxic Pool Security Guard
            if pool_address in [b.lower() for b in BLACKLISTED_POOLS]:
                self._send_json(200, {"decision": "BLACKLIST_AND_ABORT", "reason": "Pool matches confirmed toxic/drained contract history."})
                return

            # 3. Liquidity Gate ($5,000 min floor)
            if pool_liquidity_usd < 5000.0:
                self._send_json(200, {"decision": "SKIP", "reason": f"Pool liquidity ${pool_liquidity_usd:,.2f} below $5,000 safety bar."})
                return

            # 4. Token Address Validation
            if base_token not in POLYGON_TOKENS or quote_token not in POLYGON_TOKENS:
                self._send_json(200, {"decision": "REJECT", "reason": "Unofficial or unverified token contract."})
                return

            # 5. Profitability & Execution Gate
            if spread_pct >= 0.5:
                self._send_json(200, {"decision": "EXECUTE", "reason": f"Spread {spread_pct}% verified safe. Proceeding with trade."})
            else:
                self._send_json(200, {"decision": "SKIP", "reason": f"Spread {spread_pct}% below minimum profitability threshold."})
                
        except Exception as e:
            self._send_json(500, {"error": str(e)})

    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
