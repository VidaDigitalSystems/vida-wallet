#!/usr/bin/env python3
"""Wallet RPC Server — marketplace payment bridge backend.

Opens the wallet on startup with a password from env var, then exposes
simple HTTP endpoints for the marketplace PaymentBridge to call.

Usage:
    VIDA_WALLET=~/.vida/wallet.json \
    WALLET_PASSWORD=spock-wallet-2026-01 \
    python3 wallet_rpc_server.py --port 8766
"""

from __future__ import annotations
import json, os, sys, logging
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# ── Config ──
WALLET_PATH = os.environ.get("VIDA_WALLET", os.path.expanduser("~/.vida/wallet.json"))
WALLET_PASSWORD = os.environ.get("WALLET_PASSWORD", "")
PORT = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == "--port" else 8766

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
log = logging.getLogger("wallet-rpc")

# ── Add wallet to path ──
WALLET_ROOT = Path("/tmp/vida-wallet")
if WALLET_ROOT.is_dir() and str(WALLET_ROOT) not in sys.path:
    sys.path.insert(0, str(WALLET_ROOT))

# ── Wallet singleton ──
_wallet = None
_tx_mgr = None


def _get_wallet():
    global _wallet
    if _wallet is not None:
        return _wallet
    if not WALLET_PASSWORD:
        raise RuntimeError("WALLET_PASSWORD env var not set")
    from vida.secure_wallet import SecureVida
    _wallet = SecureVida(WALLET_PATH, password=WALLET_PASSWORD)
    log.info("Wallet unlocked: %s (network=%s)", _wallet.address, _wallet.network)
    return _wallet


def _get_tx_mgr():
    global _tx_mgr
    if _tx_mgr is not None:
        return _tx_mgr
    from vida.transactions import VidaTransactor
    _tx_mgr = VidaTransactor(_get_wallet())
    return _tx_mgr


def _do_send(destination: str, amount_sompi: int) -> dict:
    """Synchronously call the async VidaTransactor.send()."""
    import asyncio
    tx_mgr = _get_tx_mgr()
    result = asyncio.run(tx_mgr.send(destination, amount_sompi / 1e8))
    # SendResult is a dataclass with: success, txid, amount_kas, to_address, fee_kas, error, verified_on_network
    return {
        "ok": result.success,
        "txid": result.txid or "",
        "amount_sompi": amount_sompi,
        "destination": destination,
        "verified": result.verified_on_network,
        "error": result.error or "",
    }


class WalletHandler(BaseHTTPRequestHandler):
    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            self._json({"ok": True, "address": _get_wallet().address, "network": _get_wallet().network})
            return
        if path == "/balance":
            self._json({"ok": True, "address": _get_wallet().address, "balance": "check via kaspa.org API"})
            return
        self._json({"error": "Not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length).decode()) if length else {}

        if path == "/send":
            destination = body.get("destination", "")
            amount_sompi = int(body.get("amount_sompi", 0))
            if not destination or amount_sompi <= 0:
                self._json({"error": "destination and amount_sompi required"}, 400)
                return
            try:
                result = _do_send(destination, amount_sompi)
                log.info("SENT: %d sompi → %s (txid=%s)", amount_sompi, destination, result["txid"])
                self._json(result)
            except Exception as e:
                log.error("Send failed: %s", e)
                self._json({"error": str(e)}, 500)
            return

        self._json({"error": "Not found"}, 404)

    def log_message(self, *args):
        pass  # Don't log every request to stderr


def main():
    if not Path(WALLET_PATH).is_file():
        print(f"Wallet not found: {WALLET_PATH}")
        sys.exit(1)
    if not WALLET_PASSWORD:
        print("Set WALLET_PASSWORD env var")
        sys.exit(1)

    # Verify wallet unlocks on startup
    try:
        w = _get_wallet()
        print(f"Wallet unlocked: {w.address} ({w.network})")
    except Exception as e:
        print(f"Failed to unlock wallet: {e}")
        sys.exit(1)

    server = HTTPServer(("127.0.0.1", PORT), WalletHandler)
    log.info("Wallet RPC running on http://127.0.0.1:%d", PORT)
    print(f"Wallet RPC: http://127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()