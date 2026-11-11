# Security Policy

## Supported versions

Vida Wallet's `main` branch is the only supported version. Security fixes land on `main` and are released as soon as practical.

## Reporting a vulnerability

**Do not open a public issue for a vulnerability.**

Use GitHub's private vulnerability reporting: [Security Advisories](https://github.com/VidaDigitalSystems/vida-wallet/security/advisories/new). You can also contact the maintainers directly through the Vida Digital Systems organization.

Please include: what you found, how you found it, how you reproduced it, and what you think the impact is. We will acknowledge within a few days and coordinate a fix and disclosure.

## Scope

In scope:

- Extraction of the long-term seed or private keys from the encrypted store without the passphrase
- Encryption weaknesses in the encrypted store (AES-256-GCM with scrypt KDF)
- Session-grant bypass beyond documented limits: a session exceeding its time-box, per-tx cap, per-day cap, or destination allow-list without the owner's confirmation
- Transaction-construction bugs that lose funds or send funds to the wrong destination
- The RPC server exposing anything beyond localhost when it is documented as localhost-only
- The dashboard UI leaking secrets or session material to unintended parties

Out of scope:

- The session model is policy-enforced, not cryptographic: a reader of the session file (mode 0600) can extract the session key. This is documented in the README and is a known limitation, not a vulnerability.
- Python cannot reliably wipe key material from RAM. This is a known limitation of the language.
- Legacy `wallet.py` stored keys unencrypted; that layer is test/legacy and is not intended for production use.
- ML-DSA (Dilithium) post-quantum keys are pre-generated and stored at rest; Kaspa consensus does not support PQ signatures yet, so they are forward-identity only. They are not a vulnerability until Kaspa activates PQ support.
- TAO (Finney) uses sr25519; ML-DSA-65 is forward identity only on that chain as well.
- Fees and the practical minimum send (roughly 0.20 KAS for a single-large-UTXO send) are Kaspa protocol behavior, not wallet bugs.
- Phishing or social engineering of the owner.
- The dashboard UI is a local-only interface; it is not a hardened multi-tenant application.

## Known limitations

- Session limits are policy-enforced, not cryptographic. The session file is mode 0600 and contains limited signing material; the long-term store stays encrypted. Treat the session file as a secret.
- The wallet is mainnet-proven and is designed for a controlled agent environment where the owner is the operator. The session model is policy-enforced by design (owner is the operator); the owner chooses how much authority the agent holds.
