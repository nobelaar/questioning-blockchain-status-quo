import json
import os
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm
from web3 import Web3


DEFAULT_TIMEOUT = 20


def _http_get_json(url: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def _require_env(name: str, value: str | None) -> str:
    if value is None or value == "":
        raise RuntimeError(f"{name} not found in environment")
    return value


def _get_head_slot(beacon_api_url: str) -> int:
    data = _http_get_json(f"{beacon_api_url}/eth/v1/beacon/headers/head")
    return int(data["data"]["header"]["message"]["slot"])


def _get_validator_pubkey(
    beacon_api_url: str, proposer_index: int, cache: dict[int, str]
) -> str:
    if proposer_index in cache:
        return cache[proposer_index]
    data = _http_get_json(
        f"{beacon_api_url}/eth/v1/beacon/states/head/validators/{proposer_index}"
    )
    pubkey = data["data"]["validator"]["pubkey"]
    cache[proposer_index] = pubkey
    return pubkey


def _fetch_beacon_proposers(
    beacon_api_url: str, start_block: int, end_block: int
) -> dict[int, dict]:
    beacon_api_url = beacon_api_url.rstrip("/")
    head_slot = _get_head_slot(beacon_api_url)
    proposer_cache: dict[int, str] = {}
    by_block: dict[int, dict] = {}
    expected_count = end_block - start_block + 1

    pbar = tqdm(total=expected_count, desc="Beacon proposers", unit="block")
    slot = head_slot
    while slot >= 0:
        try:
            data = _http_get_json(f"{beacon_api_url}/eth/v2/beacon/blocks/{slot}")
        except HTTPError as exc:
            if exc.code == 404:
                slot -= 1
                continue
            raise

        message = data.get("data", {}).get("message", {})
        body = message.get("body", {})
        exec_payload = body.get("execution_payload")
        if exec_payload:
            block_number = int(exec_payload["block_number"])
            if block_number < start_block:
                break
            if block_number <= end_block:
                proposer_index = int(message["proposer_index"])
                proposer_pubkey = _get_validator_pubkey(
                    beacon_api_url, proposer_index, proposer_cache
                )
                by_block[block_number] = {
                    "proposer_index": proposer_index,
                    "proposer_pubkey": proposer_pubkey,
                    "slot": int(message["slot"]),
                }
                pbar.update(1)
                if len(by_block) >= expected_count and start_block in by_block:
                    break

        slot -= 1

    pbar.close()
    missing = [
        block_number
        for block_number in range(start_block, end_block + 1)
        if block_number not in by_block
    ]
    if missing:
        raise RuntimeError(
            "Missing proposer info for "
            f"{len(missing)} blocks (first missing {missing[0]})."
        )
    return by_block


def _get_builder_pubkey(relay_url: str, block_number: int) -> str | None:
    if not relay_url:
        return None
    relay_url = relay_url.rstrip("/")
    url = (
        f"{relay_url}/relay/v1/data/bidtraces/"
        f"proposer_payload_delivered?block_number={block_number}"
    )
    try:
        data = _http_get_json(url)
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    if isinstance(data, list) and data:
        return data[0].get("builder_pubkey")
    return None


def fetch_blocks(
    blockchain: str,
    n_blocks: int | None = None,
    rpc_url: str | None = None,
    beacon_api_url: str | None = None,
    relay_url: str | None = None,
) -> None:
    load_dotenv()

    if n_blocks is None:
        n_blocks_env = _require_env("N_BLOCKS", os.getenv("N_BLOCKS"))
        try:
            n_blocks = int(n_blocks_env)
        except ValueError as exc:
            raise RuntimeError("N_BLOCKS must be an integer") from exc
    if n_blocks <= 0:
        raise ValueError("N_BLOCKS must be greater than 0")

    if rpc_url is None:
        rpc_url = os.getenv(f"{blockchain.upper()}_RPC_URL")
    rpc_url = _require_env(f"{blockchain.upper()}_RPC_URL", rpc_url)

    if beacon_api_url is None:
        beacon_api_url = os.getenv("BEACON_API_URL")
    if relay_url is None:
        relay_url = os.getenv("MEVBOOST_RELAY_URL")

    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": DEFAULT_TIMEOUT}))
    if not w3.is_connected():
        raise RuntimeError(f"Failed to connect to RPC at {rpc_url}")

    latest_block = w3.eth.block_number
    start_block = max(0, latest_block - n_blocks + 1)
    total_blocks = latest_block - start_block + 1

    if blockchain.lower() == "ethereum":
        beacon_api_url = _require_env("BEACON_API_URL", beacon_api_url)
        proposer_map = _fetch_beacon_proposers(
            beacon_api_url, start_block, latest_block
        )
    else:
        proposer_map = {}

    os.makedirs("data/raw", exist_ok=True)
    print(f"Fetching {total_blocks} blocks for {blockchain}")

    rows = []
    for block_number in tqdm(
        range(start_block, latest_block + 1), desc="Blocks", unit="block"
    ):
        block = w3.eth.get_block(block_number, full_transactions=False)
        timestamp = int(block["timestamp"])

        proposer_index = None
        proposer_pubkey = None
        slot = None
        if proposer_map:
            proposer_info = proposer_map[block_number]
            proposer_index = proposer_info["proposer_index"]
            proposer_pubkey = proposer_info["proposer_pubkey"]
            slot = proposer_info["slot"]
            proposer = proposer_pubkey
        else:
            proposer = block.get("miner")

        builder_pubkey = _get_builder_pubkey(relay_url, block_number)

        rows.append(
            {
                "block_number": block_number,
                "timestamp": timestamp,
                "proposer": proposer,
                "proposer_index": proposer_index,
                "proposer_pubkey": proposer_pubkey,
                "builder_pubkey": builder_pubkey,
                "slot": slot,
            }
        )

    df = pd.DataFrame(rows)
    out_path = f"data/raw/{blockchain}_blocks.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved {len(rows)} blocks to {out_path}")
