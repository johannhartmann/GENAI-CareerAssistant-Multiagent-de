import os
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.document_loaders import FireCrawlLoader

from dotenv import load_dotenv

load_dotenv()

class SerperClient:
    """
    Ein Client für die Durchführung von Google-Suchen mit der Serper-API.

    Dieser Client bietet synchrone und asynchrone Methoden zur Durchführung von Google-Suchen
    und zum Abrufen der Suchergebnisse.

    Attribute:
        Keine

    Methoden:
        search(query, num_results): Führt eine Google-Suche für die angegebene Abfrage durch und gibt die Suchergebnisse zurück.
        search_async(query, num_results): Führt asynchron eine Google-Suche für die angegebene Abfrage durch und gibt die Suchergebnisse zurück.
    """

    def __init__(self, serper_api_key: str = os.environ.get("SERPER_API_KEY")) -> None:
        self.serper_api_key = serper_api_key

    def search(
        self,
        query,
        num_results: int = 5,
    ):
        """
        Führt eine Google-Suche für die angegebene Abfrage durch und gibt die Suchergebnisse zurück.

        Args:
            query (str): Die Suchanfrage.
            num_results (int, optional): Die Anzahl der abzurufenden Suchergebnisse. Standardmäßig GOOGLE_SEARCH_DEFAULT_RESULT_COUNT.

        Returns:
            dict: Die Suchergebnisse als Wörterbuch.

        """
        response = GoogleSerperAPIWrapper(k=num_results).results(query=query)
        # Dies dient dazu, die Antwort mit der Antwort des Google-Suchclients kompatibel zu machen
        items = response.pop("organic", [])
        response["items"] = items
        return response


class FireCrawlClient:

    def __init__(
        self, firecrawl_api_key: str = os.environ.get("FIRECRAWL_API_KEY")
    ) -> None:
        self.firecrawl_api_key = firecrawl_api_key

    def scrape(self, url):
        docs = FireCrawlLoader(
            api_key=self.firecrawl_api_key, url=url, mode="scrape"
        ).lazy_load()

        page_content = ""
        for doc in docs:
            page_content += doc.page_content

        # Begrenzung auf 10.000 Zeichen
        return page_content[:10000]
