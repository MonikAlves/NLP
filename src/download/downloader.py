import asyncio
import random
import re
from curl_cffi.requests import AsyncSession
from loguru import logger
from typing import Optional, Tuple


class Downloader:
    def __init__(self):
        self._session: Optional[AsyncSession] = None
        self._lock = asyncio.Lock()

    async def get_session(self) -> AsyncSession:
        current_loop = asyncio.get_running_loop()
        async with self._lock:
            if self._session is None or self._session.loop != current_loop:
                if self._session:
                    try: await self._session.close()
                    except: pass
                self._session = AsyncSession(impersonate="chrome120", verify=False)
            return self._session

    async def close(self):
        async with self._lock:
            if self._session:
                await self._session.close()
                self._session = None

    async def download_file(self, url: str) -> Tuple[str, Optional[bytes], Optional[str]]:
        url = re.sub(r"^(.*?)(https?://)", r"\2", url.strip())
        url = url.strip().replace("http://", "https://")
        
        await asyncio.sleep(random.uniform(0.3, 1.0))

        for attempt in range(3):
            try:
                session = await self.get_session()
                resp = await session.get(url, timeout=60, allow_redirects=True)
                
                if resp.status_code == 200:
                    return url, resp.content, None
                
                if resp.status_code == 404:
                    return url, None, "Erro 404"
                
                await asyncio.sleep(2 ** (attempt + 1))
            except Exception as e:
                logger.error(f"Erro inesperado {url}: {e}")
                await asyncio.sleep(2)

        return url, None, "Falha definitiva"
