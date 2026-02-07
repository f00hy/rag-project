from crawl4ai.processors.pdf import PDFContentScrapingStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai import (
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    MatchMode,
    AsyncWebCrawler,
)
import asyncio

browser_config = BrowserConfig(
    headless=True,
    verbose=False,
)

md_generator = DefaultMarkdownGenerator(
    content_filter=PruningContentFilter(),
    options={
        "include_sup_sub": True,
        "skip_internal_links": True,
        "images_to_alt": True,
    },
)

pdf_run_config = CrawlerRunConfig(
    url_matcher="*.pdf",
    cache_mode=CacheMode.BYPASS,
    page_timeout=30000,
    scraping_strategy=PDFContentScrapingStrategy(),
    check_robots_txt=True,
    markdown_generator=md_generator,
)

doc_run_config = CrawlerRunConfig(
    url_matcher=["*docs*", "*blog*", "*article*"],
    match_mode=MatchMode.OR,
    cache_mode=CacheMode.BYPASS,
    page_timeout=30000,
    remove_overlay_elements=True,
    exclude_external_links=True,
    preserve_https_for_internal_links=True,
    check_robots_txt=True,
    markdown_generator=md_generator,
)

api_run_config = CrawlerRunConfig(
    url_matcher=["*api*", "*.json"],
    match_mode=MatchMode.OR,
    cache_mode=CacheMode.BYPASS,
    page_timeout=30000,
    check_robots_txt=True,
    markdown_generator=md_generator,
)

default_run_config = CrawlerRunConfig(
    cache_mode=CacheMode.BYPASS,
    page_timeout=30000,
    scan_full_page=True,
    remove_overlay_elements=True,
    exclude_external_links=True,
    preserve_https_for_internal_links=True,
    check_robots_txt=True,
    markdown_generator=md_generator,
)

run_configs: list[CrawlerRunConfig] = [
    pdf_run_config,
    doc_run_config,  # Placed before to prevent API reference pages from matching as API endpoints
    api_run_config,  # API endpoints
    default_run_config,
]

# url="https://docs.astral.sh/uv/"
# url="https://api.github.com/users/hadley/orgs"
# url="https://ontheline.trincoll.edu/images/bookdown/sample-local-pdf.pdf"


async def main():
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://docs.astral.sh/uv/",
            config=pdf_run_config,
        )

        if result.success:
            print("Crawl successful.")
            with open("result.md", "w") as f:
                f.write(result.markdown.fit_markdown)
        else:
            print("Crawl failed:", result.error_message)


if __name__ == "__main__":
    asyncio.run(main())
