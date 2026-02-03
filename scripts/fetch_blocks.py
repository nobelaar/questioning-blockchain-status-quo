from web3 import Web3
import pandas as pd
import os
from dotenv import load_dotenv
from tqdm import tqdm

def fetch_blocks(blockchain: str):
    N_BLOCKS = 1000
    print(f"Fetching {N_BLOCKS} blocks for {blockchain}")
    load_dotenv()

    RPC_URL = os.getenv(f"{blockchain.upper()}_RPC_URL")

    w3 = Web3(Web3.HTTPProvider(RPC_URL))

    assert w3.is_connected()


    latest_block = w3.eth.block_number
    start_block = latest_block - N_BLOCKS + 1

    rows = []

    for block_number in tqdm(range(start_block, latest_block + 1)):
        block = w3.eth.get_block(block_number)
        rows.append({
            "block_number": block_number,
            "timestamp": block["timestamp"],
            "proposer": block.miner,
        })

    df = pd.DataFrame(rows)
    df.to_csv(f"data/raw/{blockchain}_blocks.csv", index=False)


    print(f"Saved {len(rows)} blocks to data/raw/{blockchain}_blocks.csv")