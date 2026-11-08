"""Layer 3: Wallet Service — key management, signing, and UTXO handling.

Provides wallet operations for agents:
- Key generation and storage
- KIP-0005 message signing and verification
- UTXO selection for payments
- Balance tracking
- Transaction building (unsigned)

In production, connects to a Kaspa node via the Kaspa SDK.
In development, uses a local stub mode.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .signer import (
    sign_message_kip0005, verify_message_kip0005,
    hash_kip0005, HAS_KASPA_SDK,
)

log = logging.getLogger("wallet")

WALLET_DIR = Path.home() / ".vida-commerce" / "wallets"
WALLET_DIR.mkdir(parents=True, exist_ok=True)

# ── Data Structures ──

@dataclass
class UtxoEntry:
    """A single UTXO tracked by the wallet."""
    txid: str
    index: int
    amount_sompi: int
    script_pubkey: str
    covenant_id: Optional[str] = None
    is_coinbase: bool = False
    daa_score: int = 0

@dataclass
class AgentWallet:
    """Wallet state for a single agent identity."""
    wallet_id: str
    public_key_hex: str
    address: str
    private_key_hex: str = ""  # Only stored for development wallets
    balance_sompi: int = 0
    utxos: list = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def balance_kas(self) -> float:
        return self.balance_sompi / 1e8

# ── In-Memory Registry ──

_wallets: dict[str, AgentWallet] = {}

# ── Wallet Operations ──

def create_wallet(wallet_id: str, private_key_hex: str = "") -> AgentWallet:
    """Create a new wallet. Uses Kaspa SDK for real address derivation when available."""
    # Try Kaspa SDK for real address derivation
    try:
        from kaspa import PrivateKey
        from .network_config import KASPA_NETWORK_TYPE
        if private_key_hex:
            pk = PrivateKey(private_key_hex)
        else:
            import hashlib
            seed = hashlib.sha256(f"vida-dev-wallet-{wallet_id}".encode()).digest()
            pk = PrivateKey(seed.hex())
            private_key_hex = seed.hex()
        # Derive address for current network
        addr = str(pk.to_address(KASPA_NETWORK_TYPE))
        pub_bytes = pk.to_public_key().to_string()
        wallet = AgentWallet(
            wallet_id=wallet_id,
            public_key_hex=pub_bytes,
            address=addr,
            private_key_hex=private_key_hex,
        )
        _wallets[wallet_id] = wallet
        _save(wallet)
        log.info(f"Created wallet {wallet_id} at {addr}")
        return wallet
    except ImportError:
        pass  # Fall through to stub below

    # Legacy stub fallback
    import hashlib
    seed = hashlib.sha256(f"vida-dev-wallet-{wallet_id}".encode()).digest()
    public_key_hex = seed.hex()[:64]
    if not private_key_hex:
        private_key_hex = seed.hex()
    address = f"kaspa:{wallet_id[:8]}"
    wallet = AgentWallet(
        wallet_id=wallet_id, public_key_hex=public_key_hex,
        address=address, private_key_hex=private_key_hex,
    )
    _wallets[wallet_id] = wallet
    _save(wallet)
    return wallet


def get_wallet(wallet_id: str) -> Optional[AgentWallet]:
    """Get a wallet by ID. Loads from disk if not in memory."""
    w = _wallets.get(wallet_id)
    if w:
        return w
    return _load(wallet_id)


def delete_wallet(wallet_id: str):
    """Remove a wallet from registry and disk."""
    _wallets.pop(wallet_id, None)
    path = WALLET_DIR / f"{wallet_id}.json"
    if path.exists():
        path.unlink()


def list_wallets() -> list[str]:
    """Return all known wallet IDs."""
    return list(_wallets.keys())


# ── UTXO Management ──

def update_utxos(wallet_id: str, utxos: list[UtxoEntry]):
    """Replace the UTXO set for a wallet."""
    wallet = get_wallet(wallet_id)
    if not wallet:
        log.error(f"Wallet {wallet_id} not found")
        return
    wallet.utxos = utxos
    wallet.balance_sompi = sum(u.amount_sompi for u in utxos)
    _save(wallet)
    log.info(f"Updated UTXOs for {wallet_id}: {len(utxos)} UTXOs, {wallet.balance_kas:.2f} KAS")


def select_utxos(wallet_id: str, amount_sompi: int,
                 count: int = 10) -> tuple[list[UtxoEntry], int]:
    """Select UTXOs to cover a payment. Greedy selection.

    Returns:
        (selected_utxos, total_selected_sompi)
    """
    wallet = get_wallet(wallet_id)
    if not wallet:
        return [], 0

    selected: list[UtxoEntry] = []
    total = 0
    for utxo in sorted(wallet.utxos, key=lambda u: -u.amount_sompi):
        if total >= amount_sompi:
            break
        if len(selected) >= count:
            break
        selected.append(utxo)
        total += utxo.amount_sompi

    return selected, total


def get_balance(wallet_id: str) -> tuple[int, float]:
    """Get wallet balance in sompi and KAS."""
    wallet = get_wallet(wallet_id)
    if not wallet:
        return 0, 0.0
    return wallet.balance_sompi, wallet.balance_kas


# ── Signing ──

def sign_message(wallet_id: str, raw_message: str) -> Optional[str]:
    """Sign a message using KIP-0005 format.

    Uses Kaspa SDK when available, stub otherwise.
    Compatible with standard Kaspa wallets and OpCheckSigFromStack.

    Returns hex-encoded signature or None on failure.
    """
    wallet = get_wallet(wallet_id)
    if not wallet:
        log.error(f"Wallet {wallet_id} not found")
        return None

    sig = sign_message_kip0005(raw_message, wallet.private_key_hex)
    if sig:
        log.info(f"Signed message for {wallet_id}: sig={sig[:16]}...")
    else:
        log.warning(f"Failed to sign message for {wallet_id}")
    return sig


def sign_payment(wallet_id: str, destination: str, amount_sompi: int,
                 utxos: list[UtxoEntry]) -> Optional[str]:
    """Sign a payment transaction.

    Returns hex-encoded transaction or None on failure.
    """
    wallet = get_wallet(wallet_id)
    if not wallet:
        log.error(f"Wallet {wallet_id} not found")
        return None

    # In production, build and sign a Kaspa transaction
    # 1. Build transaction from UTXOs
    # 2. Sign inputs
    # 3. Return serialized transaction
    log.info(f"Signing payment: {amount_sompi} sompi → {destination}")
    return "00" * 100  # Stub — placeholder transaction


# ── Persistence ──

def _serialize(wallet: AgentWallet) -> dict:
    return {
        "wallet_id": wallet.wallet_id,
        "address": wallet.address,
        "public_key_hex": wallet.public_key_hex,
        "private_key_hex": wallet.private_key_hex,
        "balance_sompi": wallet.balance_sompi,
        "created_at": wallet.created_at,
        "utxos": [
            {
                "txid": u.txid,
                "index": u.index,
                "amount_sompi": u.amount_sompi,
                "script_pubkey": u.script_pubkey,
                "covenant_id": u.covenant_id,
                "is_coinbase": u.is_coinbase,
                "daa_score": u.daa_score,
            }
            for u in wallet.utxos
        ],
    }


def _save(wallet: AgentWallet):
    path = WALLET_DIR / f"{wallet.wallet_id}.json"
    with open(path, "w") as f:
        json.dump(_serialize(wallet), f, indent=2)


def _load(wallet_id: str) -> Optional[AgentWallet]:
    path = WALLET_DIR / f"{wallet_id}.json"
    if not path.exists():
        return None
    with open(path) as f:
        data = json.load(f)
    wallet = AgentWallet(
        wallet_id=data["wallet_id"],
        public_key_hex=data["public_key_hex"],
        address=data["address"],
        private_key_hex=data.get("private_key_hex", ""),
        balance_sompi=data.get("balance_sompi", 0),
        utxos=[
            UtxoEntry(
                txid=u["txid"],
                index=u["index"],
                amount_sompi=u["amount_sompi"],
                script_pubkey=u["script_pubkey"],
                covenant_id=u.get("covenant_id"),
                is_coinbase=u.get("is_coinbase", False),
                daa_score=u.get("daa_score", 0),
            )
            for u in data.get("utxos", [])
        ],
    )
    _wallets[wallet_id] = wallet
    return wallet


def load_all_wallets() -> int:
    """Load all persisted wallets from disk. Returns count."""
    count = 0
    for path in WALLET_DIR.glob("*.json"):
        w = _load(path.stem)
        if w:
            _wallets[w.wallet_id] = w
            count += 1
    return count