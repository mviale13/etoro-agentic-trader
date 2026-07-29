import asyncio
import json
import uuid

import httpx

from app.config import Settings


async def main() -> None:
    settings = Settings()

    if not settings.etoro_api_key or not settings.etoro_user_key:
        raise RuntimeError("Missing ETORO_API_KEY or ETORO_USER_KEY")

    headers = {
        "x-api-key": settings.etoro_api_key,
        "x-user-key": settings.etoro_user_key,
        "x-request-id": str(uuid.uuid4()),
    }

    url = f"{settings.etoro_base_url}/api/v1/watchlists"

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

    with open("etoro-watchlists-response.json", "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    print("Saved: etoro-watchlists-response.json")
    print("Response type:", type(data).__name__)

    if isinstance(data, dict):
        print("Top-level keys:", list(data.keys()))


if __name__ == "__main__":
    asyncio.run(main())
