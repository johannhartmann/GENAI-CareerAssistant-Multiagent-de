from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.language_models.chat_models import BaseChatModel
from typing import List

from members import get_team_members_details
from prompts import get_supervisor_prompt_template, get_finish_step_prompt
from schemas import RouteSchema


def get_supervisor_chain(llm: BaseChatModel):
    """
    Gibt eine Supervisor-Kette zurück, die ein Gespräch zwischen Mitarbeitern verwaltet.

    Die Supervisor-Kette ist verantwortlich für die Verwaltung eines Gesprächs zwischen einer Gruppe
    von Mitarbeitern. Sie fordert den Supervisor auf, den nächsten handelnden Mitarbeiter auszuwählen, und
    jeder Mitarbeiter führt eine Aufgabe aus und antwortet mit seinen Ergebnissen und seinem Status. Das
    Gespräch wird fortgesetzt, bis der Supervisor beschließt, es zu beenden.

    Returns:
        supervisor_chain: Eine Kette von Prompts und Funktionen, die das Gespräch
                          zwischen dem Supervisor und den Mitarbeitern handhaben.
    """

    team_members = get_team_members_details()

    # Generiere den formatierten String
    formatted_string = ""
    for i, member in enumerate(team_members):
        formatted_string += (
            f"**{i+1} {member['name']}**\nRolle: {member['description']}\n\n"
        )

    # Entferne die abschließende neue Zeile
    formatted_members_string = formatted_string.strip()
    system_prompt = get_supervisor_prompt_template()

    options = [member["name"] for member in team_members]
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                """
                
                Einige zu befolgende Schritte:
                - Verkomplizieren Sie das Gespräch nicht unnötig.
                - Wenn der Benutzer darum bittet, etwas im Web zu suchen, holen Sie die Informationen und zeigen Sie sie an.
                - Wenn der Benutzer darum bittet, den Lebenslauf zu analysieren, analysieren Sie ihn einfach, seien Sie nicht übermäßig schlau und tun Sie nichts anderes.
                - Rufen Sie den Chatbot-Agenten nicht auf, wenn der Benutzer nicht aus dem obigen Gespräch fragt.
                
                Strafpunkte werden vergeben, wenn Sie die obigen Schritte nicht befolgen.
                Wer sollte angesichts des obigen Gesprächs als Nächstes handeln?
                "Oder sollten wir BEENDEN? Wählen Sie eines aus: {options}.
                 Tun Sie nur das, worum gebeten wurde, und weichen Sie nicht von den Anweisungen ab. Halluzinieren Sie nicht oder 
                 erfinden Sie keine Informationen.""",
            ),
        ]
    ).partial(options=str(options), members=formatted_members_string)

    supervisor_chain = prompt | llm.with_structured_output(RouteSchema)

    return supervisor_chain


def get_finish_chain(llm: BaseChatModel):
    """
    Wenn der Supervisor beschließt, das Gespräch zu beenden, wird diese Kette ausgeführt.
    """
    system_prompt = get_finish_step_prompt()
    prompt = ChatPromptTemplate.from_messages(
        [
            MessagesPlaceholder(variable_name="messages"),
            ("system", system_prompt),
        ]
    )
    finish_chain = prompt | llm
    return finish_chain
