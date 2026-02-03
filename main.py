import scripts.fetch_blocks as fetch_blocks
from os import getenv
from dotenv import load_dotenv
load_dotenv()
if not getenv("ETHEREUM_RPC_URL"):
    raise RuntimeError("ETHEREUM_RPC_URL not found in .env")

def main():
    
    fetch_blocks.fetch_blocks("ethereum")


if __name__ == "__main__":
    main()
