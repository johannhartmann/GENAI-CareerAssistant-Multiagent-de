from ast import List
from typing import Literal, Optional, List, Union
from pydantic import BaseModel, Field


class RouteSchema(BaseModel):
    next_action: Literal[
        "ResumeAnalyzer",
        "CoverLetterGenerator",
        "JobSearcher",
        "WebResearcher",
        "ChatBot",
        "Finish",
    ] = Field(
        ...,
        title="Nächster",
        description="Wählen Sie die nächste Rolle aus",
    )


class JobSearchInput(BaseModel):
    keywords: str = Field(
        description="Schlüsselwörter, die die Jobrolle beschreiben. (Wenn der Benutzer nach einer Rolle in einem bestimmten Unternehmen sucht, geben Sie das Unternehmen mit den Schlüsselwörtern an)"
    )
    location_name: Optional[str] = Field(
        description='Name des Ortes, in dem gesucht werden soll. Beispiel: "Kiew Stadt, Ukraine".'
    )
    employment_type: Optional[
        List[
            Literal[
                "full-time",
                "contract",
                "part-time",
                "temporary",
                "internship",
                "volunteer",
                "other",
            ]
        ]
    ] = Field(description="Spezifische Art(en) von Jobs, nach denen gesucht werden soll.")
    limit: Optional[int] = Field(
        default=5, description="Maximale Anzahl der abzurufenden Jobs."
    )
    job_type: Optional[List[Literal["onsite", "remote", "hybrid"]]] = Field(
        description="Filter für Remote-Jobs, Vor-Ort-Jobs oder Hybrid-Jobs"
    )
    experience: Optional[
        List[
            Literal[
                "internship",
                "entry-level",
                "associate",
                "mid-senior-level",
                "director",
                "executive",
            ]
        ]
    ] = Field(
        description='Filter nach Erfahrungsstufen. Optionen sind "Praktikum", "Einstiegsniveau", "Associate", "mittleres bis gehobenes Niveau", "Direktor", "Führungskraft". Geben Sie die genauen Argumente an'
    )
    listed_at: Optional[Union[int, str]] = Field(
        default=86400,
        description="Maximale Anzahl von Sekunden seit der Jobveröffentlichung. 86400 filtert Jobausschreibungen, die in den letzten 24 Stunden veröffentlicht wurden.",
    )
    distance: Optional[Union[int, str]] = Field(
        default=25,
        description="Maximale Entfernung vom Standort in Meilen. Wenn nicht angegeben oder 0, wird der Standardwert von 25 Meilen angewendet.",
    )
