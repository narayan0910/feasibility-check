import asyncio
import logging
from ddgs import DDGS
from crawl4ai import AsyncWebCrawler


# Configure logging
logging.basicConfig(
    filename="scraper.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


def ddgs_url_scrapper(query):
    logging.info(f"Searching DDGS for query: {query}")

    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=10))

    urls = []
    for item in results:
        data = {
            "title": item["title"],
            "url": item["href"],
            "snippet": item["body"]
        }

        urls.append(data)

        logging.info(
            f"Found result | Title: {data['title']} | URL: {data['url']}"
        )

    return urls


async def crawler_service(urls):
    content_results = []
    async with AsyncWebCrawler() as crawler:
        for item in urls:
            title = item["title"]
            url = item["url"]

            print(f"\n=== {title} ===")
            print(f"URL: {url}\n")

            logging.info(f"Starting crawl for: {url}")

            try:
                result = await crawler.arun(url=url)

                markdown = result.markdown or ""

                print(markdown[:1000])
                print("\n" + "-" * 80)

                logging.info(
                    f"Successfully crawled: {url} | "
                    f"Markdown length: {len(markdown)}"
                )

                # Save crawled content to log file
                logging.info(
                    f"Crawled content for {url}:\n"
                    f"{markdown[:2000]}"
                )
                
                content_results.append(
                    f"Source: {title} ({url})\nContent snippet: {markdown[:2000]}"
                )

            except Exception as e:
                print(f"Failed to crawl {url}")
                print(e)

                logging.error(
                    f"Failed to crawl {url} | Error: {str(e)}",
                    exc_info=True
                )

            print("-" * 80)
            
    return "\n\n---\n\n".join(content_results)


if __name__ == "__main__":
    logging.info("Program started")

    while True:
        query = input("Idea: ").strip()

        if query.lower() == "exit":
            logging.info("User exited program")
            break

        reddit_query = f"{query} site:reddit.com"

        try:
            urls = ddgs_url_scrapper(reddit_query)

            if not urls:
                print("No results found.")
                logging.warning(f"No results found for query: {reddit_query}")
                continue

            asyncio.run(crawler_service(urls))

        except Exception as e:
            print(f"Unexpected error: {e}")
            logging.error(
                f"Unexpected error for query '{reddit_query}': {str(e)}",
                exc_info=True
            )

        command = input("\nDo you want to continue? (yes/no): ").strip().lower()

        if command in ["no", "n", "exit"]:
            logging.info("User chose to stop")
            break

    logging.info("Program ended")
