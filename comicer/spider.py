import asyncio
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, Optional, Set

from playwright.async_api import (
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)
from pydantic import HttpUrl, parse_obj_as

from comicer.config import CONFIG
from comicer.source import Source


class Spider:
    def __init__(
        self, source: Source, save_path: Optional[Path] = None
    ) -> None:
        self.source = source
        self.save_path = save_path or CONFIG.save_path
        self.state_file = Path(
            os.path.join(
                CONFIG.state_path, str(self.source.start_url.host) + ".json"
            )
        )
        if not self.state_file.parent.exists():
            os.makedirs(self.state_file.parent, exist_ok=True)
        self.favorite_urls: Set[str] = set()
        self.download_urls: DefaultDict[str, Set[str]] = defaultdict(set)

    async def start(self):
        async with async_playwright() as p:
            page = await self.init_login_page(p)
            await self.goto(page, self.source.start_url)
            await self.parse_favorite(page)
            async for url in self.yield_favorite_url():
                await self.goto(page, url)
                await self.parse_download(page)
            await self.download(page)

    async def download(self, page: Page):
        async for title in self.yield_tile():
            title_path = os.path.join(
                self.save_path, str(self.source.start_url.host), title
            )
            url_file_path = os.path.join(title_path, "url.json")
            exist_url_list = []
            if os.path.exists(url_file_path):
                with open(url_file_path, "r") as f:
                    data = json.load(f)
                    exist_url_list.extend(data)
            os.makedirs(title_path, exist_ok=True)
            async for url in self.yield_download_url(title):
                if url in exist_url_list:
                    continue
                exist_url_list.append(url)
                async with page.expect_download(timeout=0) as download_info:
                    try:
                        await self.goto(page, url)
                    except Exception:
                        pass
                download = await download_info.value
                file_path = os.path.join(
                    title_path, download.suggested_filename
                )
                await download.save_as(file_path)
            with open(url_file_path, "w") as f:
                exist_url_list = list(set(exist_url_list))
                json.dump(exist_url_list, f)

    async def init_login_page(self, p: Playwright):
        context = await self.get_context(p)
        page = await self.get_page(context)
        if not await self.is_login(page):
            await self.login(page)
            await context.storage_state(path=self.state_file)
        return page

    async def get_context(self, p: Playwright):
        browser_type = self.browser_type(p)
        browser = await browser_type.launch(headless=True)
        if os.path.exists(self.state_file):
            context = await browser.new_context(storage_state=self.state_file)
        else:
            context = await browser.new_context()
        return context

    async def parse_download(self, page: Page):
        title = await self.parse_title(page)
        if not title:
            return
        urls = [
            await element.get_attribute("href")
            for element in await page.query_selector_all(
                self.source.download_ulr_selector
            )
        ]
        self.download_urls[title].update([url for url in urls if url])

    async def parse_title(self, page: Page):
        try:
            return await page.locator(
                self.source.title_selector
            ).text_content()
        except Exception:
            return None

    async def parse_favorite(self, page: Page):
        urls = [
            await element.get_attribute("href")
            for element in await page.query_selector_all(
                self.source.favorite_url_selector
            )
        ]
        self.favorite_urls.update([url for url in urls if url])

    async def goto(self, page: Page, url: HttpUrl):
        res = await page.goto(url)
        await asyncio.sleep(1)
        return res

    async def get_page(self, context: BrowserContext):
        if not context.pages:
            page = await context.new_page()
        else:
            page = context.pages[0]
        page.set_default_timeout(30000)
        return page

    def browser_type(self, playwrite: Playwright):
        return playwrite.chromium

    async def login(self, page: Page):
        assert self.source.username
        assert self.source.password
        await self.goto(page, self.source.login_url)
        await page.locator(self.source.username_selector).fill(
            self.source.username
        )
        await page.locator(self.source.password_selector).fill(
            self.source.password.get_secret_value()
        )
        await page.locator(self.source.login_submit_selector).click()
        if not await self.is_login(page):
            raise Exception("login failed")

    async def is_login(self, page: Page):
        res = await self.goto(page, self.source.start_url)
        return res and res.url == str(self.source.start_url)

    async def yield_tile(self):
        for title in list(self.download_urls.keys()):
            yield title

    async def yield_download_url(self, title: str):
        for url in list(self.download_urls[title]):
            try:
                yield parse_obj_as(HttpUrl, self.absolute_url(url))
            except Exception:
                continue

    async def yield_favorite_url(self):
        for url in self.favorite_urls:
            try:
                yield parse_obj_as(HttpUrl, self.absolute_url(url))
            except Exception:
                continue

    def absolute_url(self, url: str):
        scheme = self.source.start_url.scheme
        host = self.source.start_url.host
        if not host:
            return url
        if not url.startswith("https://") and not url.startswith("http://"):
            return scheme + "://" + host + url
        return url


class MoxMoeSpider(Spider):
    def __init__(self) -> None:
        assert CONFIG.mox
        super().__init__(
            CONFIG.mox.source, CONFIG.mox.save_path or CONFIG.save_path
        )


async def run():
    spider = MoxMoeSpider()
    await spider.start()


if __name__ == "__main__":
    asyncio.run(run())
