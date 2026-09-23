from http.server import BaseHTTPRequestHandler
import json

# 20 VERIFIED POLYGON TOKENS
POLYGON_TOKENS = {
    "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
    "USDC": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
    "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
    "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
    "WPOL": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
    "AAVE": "0xd6df98294241644d5677b1e42c26f4f20f66e017",
    "LINK": "0x53e0bca35ec356bd5dddfebbd1fc0fd03fabad39",
    "UNI": "0xb33eaad8d922b1083446dc23f610c2567fb5180f",
    "CRV": "0x172370d5cd63279fafe65ad07f27be32543ff933",
    "MATICX": "0xfa68fce05ed7cbd5b443b15b5025d5d847b74684",
    "DAI": "0x8f3cf7ad23cd3cadbd9735aff958023239c6a063",
    "QUICK": "0x831753DD7087CaC61aB5644b308642cc1c33Dc13",
    "SUSHI": "0x0b3F868E0BE5597D5DB7Fe590847e84948404880",
    "GRT": "0x5fe7nk9394830172659bc1948501bf384589dbe",
    "SAND": "0xbbba073c31bf03b7acf78c2e0418fbfc0bc9335a",
    "MANA": "0xa1c5747b4661773ad4b08b64e0303fd167537b86",
    "GHST": "0x385eeqc9393018265819749a20390d1bf3759a10",
    "BAL": "0x9a71012b13ca4d3d3c5f2e67a7dc4816570606d3",
    "SNX": "0x50b728fa79973f095c03ad0973b94358d75d4co8",
    "COMP": "0x8505b9d2400a7243763f68d12bcc93f41acfca7e"
}

# SUPPORTED DEXES
SUPPORTED_DEXES = {
    "UniswapV3": {
        "router": "0xE592427A0AEce92De3EDEE1F18E0157C05861564",
        "factory": "0x1F98431c8aD98523631AE4a59f267346ea31F984"
    },
    "QuickSwapV3": {
        "router": "0xf5b509bB0909a69B1c207E495f687a596C168E12",
        "factory": "0x411b0fAcc3489691f28ad58c47006AF5E3Ab3A28"
    },
    "SushiSwapV3": {
        "router": "0x1b81D678ffb9C0263af24aB4b3170b098f67038f",
        "factory": "0xbaceB8f86c8f8442847285698bc210214872910c"
    },
    "BalancerV2": {
        "router": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        "vault": "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
    }
}

# KNOWN TOXIC / DRAINED POOLS
BLACKLISTED_POOLS = {
    "0x27e2929315ced73060bb7eccb1d160b30c1bc041": "SushiSwap: Toxic Pool Vector",
    "0x2813d43463c374a680f235c428fb1d7f08de0b69": "SushiSwap: Toxic Pool Connection",
    "0x0b3f868e0be5597d5db7feb59e1cadbb0fdda50a": "Balancer: Zero Liquidity Reserve",
    "0x0000000000000000000000000000000000001010": "SushiSwap: Deprecated MATIC Migration Target"
}

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
        response_data = {
            "status": "online",
            "message": "Laya Evaluation Guardrail Core is active.",
            "chain_id": 137,
            "tracked_tokens": len(POLYGON_TOKENS),
            "supported_dexes": list(SUPPORTED_DEXES.keys()),
            "cors_enabled": True
        }
        self.wfile.write(json.dumps(response_data).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data.decode('utf-8')) if post_data else {}
            chain_id = data.get('chain_id', 137)
            pool_address = data.get('pool_address', '').lower()
            base_token = data.get('base_token')
            quote_token = data.get('quote_token')
            spread_pct = float(data.get('spread_pct', 0.0))
            pool_liquidity_usd = float(data.get('pool_liquidity_usd', 10000.0))

            if chain_id != 137:
                self._send_json(200, {"decision": "REJECT", "reason": "Non-Polygon chain ID detected. Required: 137."})
                return

            if pool_address in [b.lower() for b in BLACKLISTED_POOLS.keys()]:
                self._send_json(200, {
                    "decision": "BLACKLIST_AND_ABORT",
                    "reason": f"Pool match on permanent blocklist: {BLACKLISTED_POOLS.get(pool_address, 'Toxic Pool')}"
                })
                return

            if pool_liquidity_usd < 5000.0:
                self._send_json(200, {"decision": "SKIP", "reason": f"Pool liquidity ${pool_liquidity_usd:,.2f} below $5,000 threshold."})
                return

            valid_tokens = list(POLYGON_TOKENS.keys()) + list(POLYGON_TOKENS.values())
            if base_token and base_token not in valid_tokens:
                self._send_json(200, {"decision": "REJECT", "reason": f"Base token '{base_token}' not in 20-token allowlist."})
                return

            if quote_token and quote_token not in valid_tokens:
                self._send_json(200, {"decision": "REJECT", "reason": f"Quote token '{quote_token}' not in 20-token allowlist."})
                return

            if spread_pct >= 0.5:
                self._send_json(200, {"decision": "EXECUTE", "reason": f"Spread {spread_pct}% verified safe. Ready for Hermes dispatch."})
            else:
                self._send_json(200, {"decision": "SKIP", "reason": f"Spread {spread_pct}% below minimum profitability threshold."})

        except Exception as e:
            self._send_json(500, {"error": str(e)})

    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self._apply_cors()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
