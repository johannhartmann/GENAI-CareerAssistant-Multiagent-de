# define tools
import os
import asyncio
from dotenv import load_dotenv
from langchain.pydantic_v1 import Field
from langchain.tools import BaseTool, tool, StructuredTool
from data_loader import load_resume, write_cover_letter_to_doc
from schemas import JobSearchInput
from search import get_job_ids, fetch_all_jobs
from utils import FireCrawlClient, SerperClient

load_dotenv()


# Job search tools
def linkedin_job_search(
    keywords: str,
    location_name: str = None,
    job_type: str = None,
    limit: int = 5,
    employment_type: str = None,
    listed_at=None,
    experience=None,
    distance=None,
) -> dict:  # type: ignore
    """
    Suche auf LinkedIn nach Stellenangeboten basierend auf bestimmten Kriterien. Gibt detaillierte Stellenangebote zurück.
    """
    job_ids = get_job_ids(
        keywords=keywords,
        location_name=location_name,
        employment_type=employment_type,
        limit=limit,
        job_type=job_type,
        listed_at=listed_at,
        experience=experience,
        distance=distance,
    )
    job_desc = asyncio.run(fetch_all_jobs(job_ids))
    return job_desc


def get_job_search_tool():
    """
    Erstelle ein Tool für die JobPipeline-Funktion.
    Rückgabe:
    StructuredTool: Ein strukturiertes Tool für die JobPipeline-Funktion.
    """
    job_pipeline_tool = StructuredTool.from_function(
        func=linkedin_job_search,
        name="JobSearchTool",
        description="Suche auf LinkedIn nach Stellenangeboten basierend auf bestimmten Kriterien. Gibt detaillierte Stellenangebote zurück",
        args_schema=JobSearchInput,
    )
    return job_pipeline_tool


# Resume Extraction Tool
class ResumeExtractorTool(BaseTool):
    """
    Extrahiere den Inhalt eines Lebenslaufs aus einer PDF-Datei.
    Rückgabe:
        dict: Der extrahierte Inhalt des Lebenslaufs.
    """

    name: str = "ResumeExtractor"
    description: str = (
        "Extrahiere den Inhalt des hochgeladenen Lebenslaufs aus einer PDF-Datei."
    )

    def extract_resume(self) -> str:
        """
        Extrahiere den Lebenslaufinhalt aus einer PDF-Datei.
        Extrahiere und strukturiere jobrelevante Informationen aus einem hochgeladenen Lebenslauf.

        Rückgabe:
        str: Der Inhalt der hervorgehobenen Fähigkeiten, Erfahrungen und Qualifikationen, die für Bewerbungen relevant sind, unter Auslassung persönlicher Informationen
        """
        text = load_resume("temp/resume.pdf")
        return text

    def _run(self) -> dict:
        return self.extract_resume()


# Cover Letter Generation Tool
@tool
def generate_letter_for_specific_job(resume_details: str, job_details: str) -> dict:
    """
    Generiere ein maßgeschneidertes Anschreiben unter Verwendung des bereitgestellten Lebenslaufs und der Stellendetails. Diese Funktion erstellt das Anschreiben als Klartext.
    Rückgabe: Ein Wörterbuch mit den Stellen- und Lebenslaufdetails zur Generierung des Anschreibens.
    """
    return {"job_details": job_details, "resume_details": resume_details}


@tool
def save_cover_letter_for_specific_job(
    cover_letter_content: str, company_name: str
) -> str:
    """
    Gibt einen Download-Link für das generierte Anschreiben zurück.
    Parameter:
    cover_letter_content: Die kombinierten Informationen aus Lebenslauf und Stellendetails zur Anpassung des Anschreibens.
    """
    filename = f"temp/{company_name}_cover_letter.docx"
    file = write_cover_letter_to_doc(cover_letter_content, filename)
    abs_path = os.path.abspath(file)
    return f"Hier ist der Download-Link: {abs_path}"


# Web Search Tools
@tool("google_search")
def get_google_search_results(
    query: str = Field(..., description="Suchanfrage für das Web")
) -> str:
    """
    Durchsuche das Web nach der gegebenen Anfrage und gib die Suchergebnisse zurück.
    """
    response = SerperClient().search(query)
    items = response.get("items")
    string = []
    for result in items:
        try:
            string.append(
                "\n".join(
                    [
                        f"Titel: {result['title']}",
                        f"Link: {result['link']}",
                        f"Ausschnitt: {result['snippet']}",
                        "---",
                    ]
                )
            )
        except KeyError:
            continue

    content = "\n".join(string)
    return content


@tool("scrape_website")
def scrape_website(url: str = Field(..., description="Zu scrapende URL")) -> str:
    """
    Scrape den Inhalt einer Website und gib den Text zurück.
    """
    try:
        content = FireCrawlClient().scrape(url)
    except Exception as exc:
        return f"Scrapen von {url} fehlgeschlagen"
    return content
