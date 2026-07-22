import httpx
import json
import hashlib
from typing import Optional
from app.core.config import settings


CHAIN_CONFIG = {
    1: {
        "name": "ethereum",
        "api_url": "https://api.etherscan.io/api",
        "api_key_env": settings.etherscan_api_key,
    },
    137: {
        "name": "polygon",
        "api_url": "https://api.polygonscan.com/api",
        "api_key_env": settings.polygonscan_api_key,
    },
    42161: {
        "name": "arbitrum",
        "api_url": "https://api.arbiscan.io/api",
        "api_key_env": settings.arbiscan_api_key,
    },
    8453: {
        "name": "base",
        "api_url": "https://api.basescan.org/api",
        "api_key_env": settings.basescan_api_key,
    },
}


class SourceRetrievalError(Exception):
    pass


class ContractNotVerifiedError(SourceRetrievalError):
    pass


class SourceRetriever:

    async def fetch_source(self, address: str, chain_id: int) -> dict:
        """
        Retrieves verified source code from block explorer API.
        Raises ContractNotVerifiedError if not verified.
        Returns dict with source, abi, compiler_version, block_number.
        """
        config = CHAIN_CONFIG.get(chain_id)
        if not config:
            raise SourceRetrievalError(f"Unsupported chain_id: {chain_id}")

        api_key = config["api_key_env"]
        if not api_key:
            raise SourceRetrievalError(f"No API key configured for chain {chain_id}")

        params = {
            "module": "contract",
            "action": "getsourcecode",
            "address": address,
            "apikey": api_key,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(config["api_url"], params=params)
            response.raise_for_status()
            data = response.json()

        if data.get("status") != "1" or not data.get("result"):
            raise SourceRetrievalError(
                f"Explorer API error: {data.get('message', 'Unknown error')}"
            )

        result = data["result"][0]
        source_code = result.get("SourceCode", "")

        if not source_code or source_code.strip() == "":
            raise ContractNotVerifiedError(
                f"Contract {address} is not verified on chain {chain_id}"
            )

        compiler_version = result.get("CompilerVersion", "").lstrip("v")
        abi = result.get("ABI", "[]")
        contract_name = result.get("ContractName", "Unknown")

        # Normalize multi-file source format (Etherscan wraps in JSON)
        if source_code.startswith("{{"):
            source_code = source_code[1:-1]

        # Parse standard-json and flatten sources
        try:
            data = json.loads(source_code)
            if "sources" in data and isinstance(data["sources"], dict):
                flattened = "\n".join(
                    source.get("content", "") for source in data["sources"].values()
                )
                source_code = flattened
        except (json.JSONDecodeError, KeyError):
            pass  # Keep as-is if not standard-json

        source_hash = hashlib.sha256(source_code.encode()).hexdigest()

        # Fetch latest block number for provenance
        block_number = await self._get_block_number(config, api_key)

        return {
            "source_code": source_code,
            "compiler_version": compiler_version,
            "abi": abi,
            "contract_name": contract_name,
            "source_hash": source_hash,
            "block_number": block_number,
        }

    async def _get_block_number(self, config: dict, api_key: str) -> Optional[int]:
        try:
            params = {
                "module": "proxy",
                "action": "eth_blockNumber",
                "apikey": api_key,
            }
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(config["api_url"], params=params)
                data = resp.json()
                hex_block = data.get("result", "0x0")
                return int(hex_block, 16)
        except Exception:
            return None


source_retriever = SourceRetriever()
