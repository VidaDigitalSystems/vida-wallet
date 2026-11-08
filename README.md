# Vida Wallet

**The free, self-custody Kaspa + TAO wallet for the Vida ecosystem.**

Vida Wallet is free and always free. It holds both **KAS** (Kaspa) and **TAO**
(Bittensor) — one wallet, both networks. Every wallet is password-encrypted at
rest with AES-256-GCM (scrypt-derived key) and secured by a 24-word BIP39 seed
phrase (256-bit entropy) that **you** hold. Vida never sees your keys.

## Security model

- **Seed phrase**: 24-word BIP39, 256-bit entropy. Owner holds it; it is
  never stored server-side.
- **Encryption at rest**: everything secret is encrypted with AES-256-GCM.
  The encryption key is derived from the owner's password via scrypt.
- **Session keys**: on unlock, only a time-boxed session file (mode 0600)
  containing the session key is written — the long-term secret remains
  useless without the password.
- **Post-quantum**: an ML-DSA (Dilithium) public key is pre-generated alongside
  every wallet, ready for when Kaspa adds PQ signature support.
- **No dust trap**: dynamic minimum-viable-send computation replaces any fixed
  dust constant (Kaspa has no consensus dust limit; the real floor for a
  single large UTXO is ~0.20 KAS).

## Components

| File | What it is |
|---|---|
| `secure_wallet.py` | `VidaWallet` — password-encrypted, seed-phrase-based wallet (create / restore / send / receive) |
| `wallet_service.py` | Wallet service for the Vida Commerce bridge (Vida-to-Vida, encrypted) |
| `wallet_rpc_server.py` | JSON-RPC server exposing wallet ops on localhost |
| `wallet_integration.py` | Integration layer for the Vida Oracle / Marketplace (incl. TAO rail) |
| `dashboard-ui.html` | Browser dashboard UI |
| `start.sh` | Service launcher (network + node endpoint via env vars) |

## Quick start

```bash
export VIDA_NETWORK=mainnet          # or testnet
export KASPA_NODE_WS=ws://127.0.0.1:17110   # your kaspad websocket
./start.sh
```

Create a wallet (the script prints the mnemonic ONCE — write it down):

```python
from secure_wallet import VidaWallet
w = VidaWallet.create(password="your-min-10-char-password")
```

Restore from an existing 24-word phrase:

```python
w = VidaWallet.create(password="...", mnemonic_phrase="word1 word2 ... word24")
```

## License

Vida Wallet is licensed under the **Business Source License 1.1 (BSL 1.1)**.
You may use it freely — including holding, sending, and receiving KAS and TAO
for yourself or your business. **You may not use this code, in whole or in
part, to build, operate, or distribute your own wallet product or wallet
service.** On the Change Date (four years after each release), the code
converts to Apache 2.0. See LICENSE for the full terms.

Contact: Vidadigitalsystems@gmail.com
