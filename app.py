from typing import Callable, TypeVar
import os
import inspect
import streamlit as st
import streamlit_analytics2 as streamlit_analytics
from dotenv import load_dotenv
from streamlit_chat import message
from streamlit_pills import pills
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
from streamlit.delta_generator import DeltaGenerator
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from custom_callback_handler import CustomStreamlitCallbackHandler
from agents import define_graph
import shutil

load_dotenv()

# Set environment variables from Streamlit secrets or .env
os.environ["LINKEDIN_EMAIL"] = st.secrets.get("LINKEDIN_EMAIL", "")
os.environ["LINKEDIN_PASS"] = st.secrets.get("LINKEDIN_PASS", "")
os.environ["LANGCHAIN_API_KEY"] = st.secrets.get("LANGCHAIN_API_KEY", "")
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv(
    "LANGCHAIN_TRACING_V2"
) or st.secrets.get("LANGCHAIN_TRACING_V2", "")
os.environ["LANGCHAIN_PROJECT"] = st.secrets.get("LANGCHAIN_PROJECT", "")
os.environ["GROQ_API_KEY"] = st.secrets.get("GROQ_API_KEY", "")
os.environ["SERPER_API_KEY"] = st.secrets.get("SERPER_API_KEY", "")
os.environ["FIRECRAWL_API_KEY"] = st.secrets.get("FIRECRAWL_API_KEY", "")
os.environ["LINKEDIN_SEARCH"] = st.secrets.get("LINKEDIN_JOB_SEARCH", "")

# Page configuration
st.set_page_config(layout="wide")
st.title("GenAI Karriere-Assistent - 👨‍💼")
st.markdown(
    "[Verbinden Sie sich mit mir auf LinkedIn](https://www.linkedin.com/in/aman-varyani-885725181/)"
)

streamlit_analytics.start_tracking()

# Setup directories and paths
temp_dir = "temp"
dummy_resume_path = os.path.abspath("dummy_resume.pdf")

if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)

# Add dummy resume if it does not exist
if not os.path.exists(dummy_resume_path):
    default_resume_path = "path/to/your/dummy_resume.pdf"
    shutil.copy(default_resume_path, dummy_resume_path)

# Sidebar - File Upload
uploaded_document = st.sidebar.file_uploader(
    "Laden Sie Ihren Lebenslauf hoch", type="pdf"
)

if not uploaded_document:
    uploaded_document = open(dummy_resume_path, "rb")
    st.sidebar.write("Verwendung eines Dummy-Lebenslaufs zu Demonstrationszwecken. ")
    st.sidebar.markdown(
        f"[Dummy-Lebenslauf anzeigen]({'https://drive.google.com/file/d/1vTdtIPXEjqGyVgUgCO6HLiG9TSPcJ5eM/view?usp=sharing'})",
        unsafe_allow_html=True,
    )

bytes_data = uploaded_document.read()

filepath = os.path.join(temp_dir, "resume.pdf")
with open(filepath, "wb") as f:
    f.write(bytes_data)

st.markdown("**Lebenslauf erfolgreich hochgeladen!**")

# Sidebar - Service Provider Selection
service_provider = st.sidebar.selectbox(
    "Dienstanbieter",
    ("groq (llama-3.1-70b-versatile)", "openai"),
)
streamlit_analytics.stop_tracking()

# Not to track the key
if service_provider == "openai":
    # Sidebar - OpenAI Configuration
    api_key_openai = st.sidebar.text_input(
        "OpenAI API-Schlüssel",
        st.session_state.get("OPENAI_API_KEY", ""),
        type="password",
    )
    model_openai = st.sidebar.selectbox(
        "OpenAI-Modell",
        ("gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"),
    )
    settings = {
        "model": model_openai,
        "model_provider": "openai",
        "temperature": 0.3,
    }
    st.session_state["OPENAI_API_KEY"] = api_key_openai
    os.environ["OPENAI_API_KEY"] = st.session_state["OPENAI_API_KEY"]

else:
    # Toggle visibility for Groq API Key input
    if "groq_key_visible" not in st.session_state:
        st.session_state["groq_key_visible"] = False

    if st.sidebar.button("Groq API-Schlüssel eingeben (optional)"):
        st.session_state["groq_key_visible"] = True

    if st.session_state["groq_key_visible"]:
        api_key_groq = st.sidebar.text_input("Groq API-Schlüssel", type="password")
        st.session_state["GROQ_API_KEY"] = api_key_groq
        os.environ["GROQ_API_KEY"] = api_key_groq

    settings = {
        "model": "llama-3.1-70b-versatile",
        "model_provider": "groq",
        "temperature": 0.3,
    }

# Sidebar - Service Provider Note
st.sidebar.markdown(
    """
    **Hinweis:** \n
    Dieses Multi-Agenten-System funktioniert am besten mit OpenAI. llama 3.1 produziert möglicherweise nicht immer optimale Ergebnisse.\n
    Jeder bereitgestellte Schlüssel wird nicht gespeichert oder geteilt, er wird nur für die aktuelle Sitzung verwendet.
    """
)
st.sidebar.markdown(
    """
    <div style="padding:10px 0;">
        Wenn Ihnen das Projekt gefällt, geben Sie einen 
        <a href="https://github.com/amanv1906/GENAI-CareerAssistant-Multiagent" target="_blank" style="text-decoration:none;">
            ⭐ auf GitHub
        </a>
    </div>
    """,
    unsafe_allow_html=True,
)

# Create the agent flow
flow_graph = define_graph()
message_history = StreamlitChatMessageHistory()

# Initialize session state variables
if "active_option_index" not in st.session_state:
    st.session_state["active_option_index"] = None
if "interaction_history" not in st.session_state:
    st.session_state["interaction_history"] = []
if "response_history" not in st.session_state:
    st.session_state["response_history"] = ["Hallo! Wie kann ich Ihnen heute helfen?"]
if "user_query_history" not in st.session_state:
    st.session_state["user_query_history"] = ["Hallo! 👋"]

# Containers for the chat interface
conversation_container = st.container()
input_section = st.container()


# Define functions used above
def initialize_callback_handler(main_container: DeltaGenerator):
    V = TypeVar("V")

    def wrap_function(func: Callable[..., V]) -> Callable[..., V]:
        context = get_script_run_ctx()

        def wrapped(*args, **kwargs) -> V:
            add_script_run_ctx(ctx=context)
            return func(*args, **kwargs)

        return wrapped

    streamlit_callback_instance = CustomStreamlitCallbackHandler(
        parent_container=main_container
    )

    for method_name, method in inspect.getmembers(
        streamlit_callback_instance, predicate=inspect.ismethod
    ):
        setattr(streamlit_callback_instance, method_name, wrap_function(method))

    return streamlit_callback_instance


def execute_chat_conversation(user_input, graph):
    callback_handler_instance = initialize_callback_handler(st.container())
    callback_handler = callback_handler_instance
    try:
        output = graph.invoke(
            {
                "messages": list(message_history.messages) + [user_input],
                "user_input": user_input,
                "config": settings,
                "callback": callback_handler,
            },
            {"recursion_limit": 30},
        )
        message_output = output.get("messages")[-1]
        messages_list = output.get("messages")
        message_history.clear()
        message_history.add_messages(messages_list)

    except Exception as exc:
        return ":( Entschuldigung, es ist ein Fehler aufgetreten. Können Sie es bitte erneut versuchen?"
    return message_output.content


# Clear Chat functionality
if st.button("Chat löschen"):
    st.session_state["user_query_history"] = []
    st.session_state["response_history"] = []
    message_history.clear()
    st.rerun()  # Refresh the app to reflect the cleared chat

# for tracking the query.
streamlit_analytics.start_tracking()

# Display chat interface
with input_section:
    options = [
        "Identifizieren Sie die wichtigsten Trends in der Technologiebranche in Bezug auf Gen AI",
        "Finden Sie aufkommende Technologien und deren potenzielle Auswirkungen auf Jobmöglichkeiten",
        "Fassen Sie meinen Lebenslauf zusammen",
        "Erstellen Sie eine Karriereweg-Visualisierung basierend auf meinen Fähigkeiten und Interessen aus meinem Lebenslauf",
        "GenAI-Jobs bei Microsoft",
        "Jobsuche für GenAI-Jobs in Deutschland",
        "Analysieren Sie meinen Lebenslauf und schlagen Sie eine passende Jobposition vor und suchen Sie nach relevanten Stellenangeboten",
        "Generieren Sie ein Anschreiben für meinen Lebenslauf",
    ]
    icons = ["🔍", "🌐", "📝", "📈", "💼", "🌟", "✉️", "🧠  "]

    selected_query = pills(
        "Wählen Sie eine Frage für die Abfrage:",
        options,
        clearable=None,  # type: ignore
        icons=icons,
        index=st.session_state["active_option_index"],
        key="pills",
    )
    if selected_query:
        st.session_state["active_option_index"] = options.index(selected_query)

    # Display text input form
    with st.form(key="query_form", clear_on_submit=True):
        user_input_query = st.text_input(
            "Abfrage:",
            value=(
                selected_query
                if selected_query
                else "Detaillierte Analyse der neuesten Entlassungsnachrichten in Indien?"
            ),
            placeholder="📝 Schreiben Sie Ihre Abfrage oder wählen Sie aus den obigen Optionen",
            key="input",
        )
        submit_query_button = st.form_submit_button(label="Senden")

    if submit_query_button:
        if not uploaded_document:
            st.error(
                "Bitte laden Sie Ihren Lebenslauf hoch, bevor Sie eine Abfrage einreichen."
            )

        elif service_provider == "openai" and not st.session_state["OPENAI_API_KEY"]:
            st.error(
                "Bitte geben Sie Ihren OpenAI API-Schlüssel ein, bevor Sie eine Abfrage einreichen."
            )

        elif user_input_query:
            # Process the query as usual if resume is uploaded
            chat_output = execute_chat_conversation(user_input_query, flow_graph)
            st.session_state["user_query_history"].append(user_input_query)
            st.session_state["response_history"].append(chat_output)
            st.session_state["last_input"] = user_input_query  # Save the latest input
            st.session_state["active_option_index"] = None

# Display chat history
if st.session_state["response_history"]:
    with conversation_container:
        for i in range(len(st.session_state["response_history"])):
            message(
                st.session_state["user_query_history"][i],
                is_user=True,
                key=str(i) + "_user",
                avatar_style="fun-emoji",
            )
            message(
                st.session_state["response_history"][i],
                key=str(i),
                avatar_style="bottts",
            )

streamlit_analytics.stop_tracking()
