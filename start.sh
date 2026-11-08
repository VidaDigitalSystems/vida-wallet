#!/bin/bash
# Vida Wallet Service

cd /usr/bin
source ../vida-venv/bin/activate

export VIDA_NETWORK=mainnet
export VIDA_PORT=8768
export KASPA_NODE_WS="${KASPA_NODE_WS:-ws://127.0.0.1:17110}"

echo "Starting vida-wallet on port 8768"
python3 -c "
from secure_wallet import VidaWallet
import time

print('🔐 VIDA WALLET SERVICE STARTING')
wallet = VidaWallet()

# Run basic wallet service
while True:
    print(f'Wallet service active - {time.strftime("%H:%M:%S")}')
    time.sleep(30)
"
