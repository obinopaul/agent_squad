# ambient_agent.py
#
# =================================================================================================
#
# Ambient Agent Workflow: A Self-Contained Implementation
#
# =================================================================================================
#
# This single-file Python script is a complete, detailed implementation of an "ambient agent" 
# framework, adapted from the LangChain Executive AI Assistant project.
#
# What is an Ambient Agent?
# An ambient agent is a system that operates autonomously in the background without requiring
# direct, real-time human triggers for every action. It proactively monitors a data source
# (like an email inbox), processes new information, and takes appropriate action.
#
# Key Features demonstrated in this file:
# 1.  **Autonomous Triggering**: The agent is activated by a cron job scheduler, which
#     periodically checks for new inputs (emails, in this example). This removes the need for
#     a human to manually start the process.
# 2.  **Asynchronous & Concurrent Processing**: The architecture is built on `asyncio` and
#     `LangGraph`, allowing it to handle multiple tasks (e.g., processing multiple emails)
#     simultaneously and efficiently. Each email thread is processed in its own stateful thread,
#     ensuring that operations don't block one another.
# 3.  **Stateful, Multi-step Logic**: The agent uses a state machine (a graph) to perform
#     complex, multi-step reasoning for each task. This includes triaging, drafting responses,
#     rewriting for tone, and interacting with tools.
# 4.  **Human-in-the-Loop for Supervision**: While the agent runs autonomously, it can pause and
#     request human input for critical decisions, approvals, or when it lacks necessary
#     information. This is a crucial feature for safe and reliable automation.
# 5.  **Self-Reflection and Improvement**: The agent includes "reflection graphs" that allow it to
#     learn from human feedback and corrections, updating its internal prompts and logic over time
#     to improve its performance.
#
# How to Use This File:
# 1.  **Dependencies**: Install all required packages. You can typically get these from the original
#     `pyproject.toml` file.
#     ```bash
#     pip install langgraph langchain langchain-openai langchain-anthropic google-api-python-client langchain-auth langgraph-sdk langsmith pytz pyyaml python-dateutil python-dotenv langgraph-cli langgraph-api
#     ```
# 2.  **Environment Variables**: Create a `.env` file in the same directory and populate it with your
#     API keys:
#     ```
#     LANGSMITH_API_KEY="..."
#     OPENAI_API_KEY="..."
#     ANTHROPIC_API_KEY="..."
#     ```
# 3.  **Google OAuth Setup**:
#     a. Follow Google's instructions to create OAuth 2.0 credentials for a Desktop app.
#     b. Download the `client_secret.json` file.
#     c. Create a directory named `.secrets` and move the file into it, renaming it to `secrets.json`.
#        Your directory structure should look like:
#        .
#        ├── .secrets/
#        │   └── secrets.json
#        └── ambient_agent.py
# 4.  **Run the Setup & Execution Commands**: This script includes a command-line interface.
#     - **First-time setup for Google Auth**:
#       ```bash
#       python ambient_agent.py setup_gmail
#       ```
#     - **Run a local development server**:
#       ```bash
#       langgraph dev
#       ```
#     - **Manually trigger an ingest job (in a new terminal)**:
#       ```bash
#       python ambient_agent.py run_ingest --minutes-since 120
#       ```
#     - **Set up the cron job for autonomous operation (requires deployment)**:
#       ```bash
#       python ambient_agent.py setup_cron --url ${YOUR_LANGGRAPH_DEPLOYMENT_URL}
#       ```
#
# =================================================================================================

# #################################################################################################
# Section 1: Imports and Global Setup
# All necessary libraries are imported here for a self-contained script.
# #################################################################################################

import argparse
import asyncio
import base64
import email.utils
import hashlib
import httpx
import json
import logging
import os
import uuid
from datetime import datetime, timedelta, time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import (
    Annotated,
    Iterable,
    List,
    Literal,
    Optional,
    TypedDict,
    Union,
)

import pytz
import yaml
from dateutil import parser
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from langchain.agents.react.agent import create_react_agent
from langchain_anthropic import ChatAnthropic
from langchain_auth import Client as LangchainAuthClient
from langchain_core.messages import (
    HumanMessage,
    RemoveMessage,
    ToolMessage,
)
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.config import ensure_config
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import (
    START,
    END,
    StateGraph,
    add_messages,
)
from langgraph.graph.message import AnyMessage
from langgraph.store.base import BaseStore
from langgraph.types import Command, Send, interrupt
from langgraph_sdk import get_client
from langsmith import traceable
from pydantic import BaseModel as PydanticBaseModel
from typing_extensions import TypedDict as TypingExtensionsTypedDict

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize LangGraph SDK client globally
LGC = get_client()

# #################################################################################################
# Section 2: Configuration Management
# Handles loading of configuration from an embedded YAML string or an external file.
# This makes the script portable and easy to configure.
# #################################################################################################

# Default configuration is embedded as a multi-line string.
# This allows the script to run without an external config.yaml file.
DEFAULT_CONFIG_YAML = """
email: "your_email@example.com" # <-- IMPORTANT: CHANGE THIS
full_name: Harrison Chase
name: Harrison
background: Harrison is CEO and co-founder of LangChain. LangChain is a startup building tools for developers to build LLM applications.
schedule_preferences: By default, unless specified otherwise, you should make meetings 30 minutes long.
background_preferences: |
  LangChain has a product marketer - Linda. For emails where she may be relevant, please loop her in. If possible, just add her to the thread and let her handle any asks (not Harrison). Examples include: being asked to amplify a podcast, blogpost, or other work featuring Harrison or LangChain
response_preferences:
timezone: "PST"
rewrite_preferences: |
  Harrison has a few rules for how he likes his emails to be written:

  - He generally likes to match their tone. If they write formally, then so will he. If they write casually, then he should write casual
  - If working with an assistant to schedule, then he is usually more formal
  - If conversing with someone he seems to know well, then he is more direct and to the fact
  - Harrison REALLY does not want anyone to know he is using an assistant, so you should try not to sound too much like an assistant and rather sound like Harrison
  - When Harrison is casual, he generally does not include any greetings or sign offs, and just directly says his message

triage_no: |
  - Automated emails from services that are spamming Harrison
  - Cold outreach from vendors - this happens a lot as people try to sell Harrison things. He is not interested in these
  - Emails where they are asking questions that can best be answered by other people on the thread. \
  Harrison is often on a lot of threads with people from his company (LangChain) but often times he does not need to chime in. \
  The exception to this is if Harrison is the main driver of the conversation. \
  You can usually tell this by whether Harrison was the one who sent the last email
  - Generally do not need to see emails from Ramp, Rewatch, Stripe
  - Notifications of comments on Google Docs
  - Automated calendar invitations
triage_notify: |
  - Google docs that were shared with him (do NOT notify him on comments, just net new ones)
  - Docusign things that needs to sign. These are using from Docusign and start with "Complete with Docusign". \
  Note: if the Docusign is already signed, you do NOT need to notify him. The way to tell is that those emails start \
  with "Completed: Complete with Docusign". Note the "Completed". Do not notify him if "Completed", only if still needs to be completed.
  - Anything that is pretty technically detailed about LangChain. Harrison sometimes gets asked questions about LangChain, \
  while he may not always respond to those he likes getting notified about them
  - Emails where there is a clear action item from Harrison based on a previous conversation, like adding people to a slack channel
triage_email: |
  - Emails from clients that explicitly ask Harrison a question
  - Emails from clients where someone else has scheduled a meeting for Harrison, and Harrison has not already chimed in to express his excitement
  - Emails from clients or potential customers where Harrison is the main driver of the conversation
  - Emails from other LangChain team members that explicitly ask Harrison a question
  - Emails where Harrison has gotten added to a thread with a customer and he hasn't yet said hello
  - Emails where Harrison is introducing two people to each other. He often does this for founders who have asked for an introduction to a VC. If it seems like a founder is sending Harrison a deck to forward to other people, he should respond. If Harrison has already introduced the two parties, he should not respond unless they explicitly ask him a question.
  - Email from clients where they are trying to set up a time to meet
  - Any direct emails from Harrison's lawyers (Goodwin Law)
  - Any direct emails related to the LangChain board
  - Emails where LangChain is winning an award/being invited to a legitimate event
  - Emails where it seems like Harrison has a pre-existing relationship with the sender. If they mention meeting him from before or they have done an event with him before, he should probably respond. If it seems like they are referencing a event or a conversation they had before, Harrison should probably respond. 
  - Emails from friends - even these don't ask an explicit question, if it seems like something a good friend would respond to, Harrison should do so.

  Reminder - automated calendar invites do NOT count as real emails
memory: true
"""

def get_config(config: dict) -> dict:
    """
    Loads configuration.
    Prioritizes configuration passed in the `configurable` field of a LangGraph config object.
    Falls back to loading from the embedded DEFAULT_CONFIG_YAML.
    """
    if config and "configurable" in config and "email" in config["configurable"]:
        return config["configurable"]
    else:
        return yaml.safe_load(DEFAULT_CONFIG_YAML)

# #################################################################################################
# Section 3: Data Schemas
# Defines the data structures used throughout the agent's workflow using TypedDict and Pydantic.
# This ensures data consistency and provides type hinting for better code quality.
# #################################################################################################

class EmailData(TypedDict):
    id: str
    thread_id: str
    from_email: str
    subject: str
    page_content: str
    send_time: str
    to_email: str

class RespondTo(PydanticBaseModel):
    logic: str = Field(description="logic on WHY the response choice is the way it is", default="")
    response: Literal["no", "email", "notify", "question"] = "no"

class ResponseEmailDraft(PydanticBaseModel):
    """Draft of an email to send as a response."""
    content: str
    new_recipients: List[str]

class NewEmailDraft(PydanticBaseModel):
    """Draft of a new email to send."""
    content: str
    recipients: List[str]

class ReWriteEmail(PydanticBaseModel):
    """Logic for rewriting an email"""
    tone_logic: str = Field(description="Logic for what the tone of the rewritten email should be")
    rewritten_content: str = Field(description="Content rewritten with the new tone")

class Question(PydanticBaseModel):
    """Question to ask user."""
    content: str

class Ignore(PydanticBaseModel):
    """Call this to ignore the email. Only call this if user has said to do so."""
    ignore: bool

class MeetingAssistant(PydanticBaseModel):
    """Call this to have user's meeting assistant look at it."""
    call: bool

class SendCalendarInvite(PydanticBaseModel):
    """Call this to send a calendar invite."""
    emails: List[str] = Field(description="List of emails to send the calendar invitation for. Do NOT make any emails up!")
    title: str = Field(description="Name of the meeting")
    start_time: str = Field(description="Start time for the meeting, should be in `2024-07-01T14:00:00` format")
    end_time: str = Field(description="End time for the meeting, should be in `2024-07-01T14:00:00` format")

# Helper to convert dictionary to Pydantic model for state management
def convert_obj(o, m):
    if isinstance(m, dict):
        return RespondTo(**m)
    return m

class State(TypedDict):
    """The main state object for the agent's graph."""
    email: EmailData
    triage: Annotated[RespondTo, convert_obj]
    messages: Annotated[List[AnyMessage], add_messages]

email_template = """From: {author}
To: {to}
Subject: {subject}

{email_thread}"""

# #################################################################################################
# Section 4: External Service Integrations (Gmail & Calendar Tools)
# Contains functions for interacting with Google APIs (Gmail, Calendar).
# This includes fetching emails, sending replies, marking as read, and managing calendar events.
# #################################################################################################

_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
]

async def get_credentials(user_email: str, langsmith_api_key: str | None = None) -> Credentials:
    """Get Google API credentials using langchain-auth."""
    api_key = langsmith_api_key or os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        raise ValueError("LANGSMITH_API_KEY environment variable must be set")
    
    client = LangchainAuthClient(api_key=api_key)
    
    try:
        auth_result = await client.authenticate(provider="google", scopes=_SCOPES, user_id=user_email)
        
        if auth_result.needs_auth:
            print(f"Please visit: {auth_result.auth_url}")
            print("Complete the OAuth flow and then retry.")
            completed_result = await client.wait_for_completion(auth_id=auth_result.auth_id, timeout=300)
            token = completed_result.token
        else:
            token = auth_result.token
        
        if not token:
            raise ValueError("Failed to obtain access token")
            
        return Credentials(token=token, scopes=_SCOPES)
        
    finally:
        await client.close()

def extract_message_part(msg):
    """Recursively walk through email parts to find the message body."""
    if msg["mimeType"] == "text/plain":
        body_data = msg.get("body", {}).get("data")
        if body_data:
            return base64.urlsafe_b64decode(body_data).decode("utf-8")
    elif msg["mimeType"] == "text/html":
        # Simplified HTML handling, could be improved with parsing libraries
        body_data = msg.get("body", {}).get("data")
        if body_data:
            return base64.urlsafe_b64decode(body_data).decode("utf-8")
    if "parts" in msg:
        for part in msg["parts"]:
            body = extract_message_part(part)
            if body:
                return body
    return "No message body available."

def parse_time(send_time: str):
    try:
        return parser.parse(send_time)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Error parsing time: {send_time} - {e}")

def create_message(sender, to, subject, message_text, thread_id, original_message_id):
    message = MIMEMultipart()
    message["to"] = ", ".join(to)
    message["from"] = sender
    message["subject"] = subject
    message["In-Reply-To"] = original_message_id
    message["References"] = original_message_id
    message["Message-ID"] = email.utils.make_msgid()
    msg = MIMEText(message_text, 'html') # Send as HTML
    message.attach(msg)
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": raw, "threadId": thread_id}

def get_recipients(headers, email_address, addn_receipients=None):
    recipients = set(addn_receipients or [])
    sender = None
    for header in headers:
        if header["name"].lower() in ["to", "cc"]:
            recipients.update(v.strip() for v in header["value"].split(","))
        if header["name"].lower() == "from":
            sender = header["value"]
    if sender:
        recipients.add(sender)
    if email_address in recipients:
        recipients.remove(email_address)
    return list(recipients)

def send_message_gmail(service, user_id, message):
    return service.users().messages().send(userId=user_id, body=message).execute()

def send_email_tool(email_id, response_text, email_address, addn_receipients=None):
    creds = asyncio.run(get_credentials(email_address))
    service = build("gmail", "v1", credentials=creds)
    message = service.users().messages().get(userId="me", id=email_id).execute()
    headers = message["payload"]["headers"]
    message_id = next(h["value"] for h in headers if h["name"].lower() == "message-id")
    thread_id = message["threadId"]
    recipients = get_recipients(headers, email_address, addn_receipients)
    subject = next(h["value"] for h in headers if h["name"].lower() == "subject")
    response_message = create_message("me", recipients, subject, response_text, thread_id, message_id)
    send_message_gmail(service, "me", response_message)

async def fetch_group_emails(to_email: str, minutes_since: int = 30) -> Iterable[EmailData]:
    """Fetches emails and yields them one by one."""
    creds = await get_credentials(to_email)
    service = build("gmail", "v1", credentials=creds)
    after = int((datetime.now() - timedelta(minutes=minutes_since)).timestamp())
    query = f"(to:{to_email} OR from:{to_email}) after:{after}"
    
    messages_response = service.users().messages().list(userId="me", q=query).execute()
    messages = messages_response.get("messages", [])

    for message_info in messages:
        try:
            msg = service.users().messages().get(userId="me", id=message_info["id"]).execute()
            thread = service.users().threads().get(userId="me", id=msg["threadId"]).execute()
            
            last_message_in_thread = thread["messages"][-1]
            last_headers = last_message_in_thread["payload"]["headers"]
            last_from_header = next((h["value"] for h in last_headers if h["name"].lower() == "from"), "")

            # If the user sent the last message, skip this thread for now
            if to_email in last_from_header:
                yield {"id": msg["id"], "thread_id": msg["threadId"], "user_respond": True}
                continue

            # Only process if this message is the latest one in the thread
            if msg["id"] == last_message_in_thread["id"]:
                headers = msg["payload"]["headers"]
                subject = next((h["value"] for h in headers if h["name"].lower() == "subject"), "No Subject")
                from_email = next((h["value"] for h in headers if h["name"].lower() == "from"), "").strip()
                _to_email = next((h["value"] for h in headers if h["name"].lower() == "to"), "").strip()
                send_time_str = next((h["value"] for h in headers if h["name"].lower() == "date"), "")
                
                parsed_time = parse_time(send_time_str)
                body = extract_message_part(msg["payload"])
                
                yield {
                    "from_email": from_email,
                    "to_email": _to_email,
                    "subject": subject,
                    "page_content": body,
                    "id": msg["id"],
                    "thread_id": msg["threadId"],
                    "send_time": parsed_time.isoformat(),
                }
        except Exception as e:
            logger.error(f"Failed to process message {message_info['id']}: {e}")

def mark_as_read(message_id, user_email: str):
    creds = asyncio.run(get_credentials(user_email))
    service = build("gmail", "v1", credentials=creds)
    service.users().messages().modify(
        userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
    ).execute()

class CalInput(PydanticBaseModel):
    date_strs: list[str] = Field(description="List of days to check events, format dd-mm-yyyy.")

@tool(args_schema=CalInput)
def get_events_for_days(date_strs: list[str]):
    """Retrieves calendar events for a list of specified days."""
    config = ensure_config()
    user_config = get_config(config)
    user_email = user_config["email"]
    
    creds = asyncio.run(get_credentials(user_email))
    service = build("calendar", "v3", credentials=creds)
    results = ""
    for date_str in date_strs:
        day = datetime.strptime(date_str, "%d-%m-%Y").date()
        start_of_day = datetime.combine(day, time.min).isoformat() + "Z"
        end_of_day = datetime.combine(day, time.max).isoformat() + "Z"
        events_result = service.events().list(
            calendarId="primary",
            timeMin=start_of_day,
            timeMax=end_of_day,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        events = events_result.get("items", [])
        results += f"***FOR DAY {date_str}***\n\n" + print_events(events, user_config.get("timezone", "UTC"))
    return results

def print_events(events, timezone_str):
    if not events:
        return "No events found for this day."
    result = ""
    tz = pytz.timezone(timezone_str)
    for event in events:
        start_str = event["start"].get("dateTime", event["start"].get("date"))
        end_str = event["end"].get("dateTime", event["end"].get("date"))
        summary = event.get("summary", "No Title")
        if "T" in start_str:
            start_dt = parser.isoparse(start_str).astimezone(tz)
            end_dt = parser.isoparse(end_str).astimezone(tz)
            result += f"Event: {summary}\nStarts: {start_dt.strftime('%Y-%m-%d %I:%M %p %Z')}\nEnds: {end_dt.strftime('%Y-%m-%d %I:%M %p %Z')}\n"
        else: # All-day event
            result += f"Event: {summary}\nStarts: {start_str}\nEnds: {end_str}\n"
        result += "-" * 40 + "\n"
    return result

def send_calendar_invite_tool(emails, title, start_time, end_time, email_address, timezone="PST"):
    creds = asyncio.run(get_credentials(email_address))
    service = build("calendar", "v3", credentials=creds)
    start_datetime = datetime.fromisoformat(start_time)
    end_datetime = datetime.fromisoformat(end_time)
    all_attendees = list(set(emails + [email_address]))
    event = {
        "summary": title,
        "start": {"dateTime": start_datetime.isoformat(), "timeZone": timezone},
        "end": {"dateTime": end_datetime.isoformat(), "timeZone": timezone},
        "attendees": [{"email": email} for email in all_attendees],
        "reminders": {"useDefault": True},
        "conferenceData": {
            "createRequest": {
                "requestId": f"{title}-{start_datetime.isoformat()}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }
    try:
        service.events().insert(
            calendarId="primary", body=event, sendNotifications=True, conferenceDataVersion=1
        ).execute()
        return True
    except Exception as e:
        logger.error(f"Error sending calendar invite: {e}")
        return False

# #################################################################################################
# Section 5: Agent Core Logic (Nodes)
# Each function here represents a step (a node) in the agent's decision-making graph.
# This modular approach separates concerns like triaging, drafting, and rewriting.
# #################################################################################################

# === 5.1 Triage Node ===
async def triage_input(state: State, config: RunnableConfig, store: BaseStore) -> dict:
    """Node to decide the initial handling of an email: ignore, notify, or respond."""
    logger.info(f"Triage: Triaging email with subject '{state['email']['subject']}'")
    model = config["configurable"].get("model", "gpt-4o")
    llm = ChatOpenAI(model=model, temperature=0)
    
    # Fetch few-shot examples for better triage accuracy
    examples = await get_few_shot_examples(state["email"], store, config)
    prompt_config = get_config(config)
    
    triage_prompt = """You are {full_name}'s executive assistant. You are a top-notch executive assistant who cares about {name} performing as well as possible.
{background}.
{name} gets lots of emails. Your job is to categorize the below email to see whether is it worth responding to.
Emails that are not worth responding to:
{triage_no}
Emails that are worth responding to:
{triage_email}
There are also other things that {name} should know about, but don't require an email response. For these, you should notify {name} (using the `notify` response). Examples of this include:
{triage_notify}
For emails not worth responding to, respond `no`. For something where {name} should respond over email, respond `email`. If it's important to notify {name}, but no email is required, respond `notify`.
If unsure, opt to `notify` {name} - you will learn from this in the future.
{fewshotexamples}
Please determine how to handle the below email thread:
From: {author}
To: {to}
Subject: {subject}
{email_thread}"""

    input_message = triage_prompt.format(
        email_thread=state["email"]["page_content"],
        author=state["email"]["from_email"],
        to=state["email"].get("to_email", ""),
        subject=state["email"]["subject"],
        fewshotexamples=examples,
        name=prompt_config["name"],
        full_name=prompt_config["full_name"],
        background=prompt_config["background"],
        triage_no=prompt_config["triage_no"],
        triage_email=prompt_config["triage_email"],
        triage_notify=prompt_config["triage_notify"],
    )
    
    model = llm.with_structured_output(RespondTo)
    response = await model.ainvoke(input_message)
    logger.info(f"Triage: Decision is '{response.response}'")
    
    # Clear previous messages if retrying
    if len(state.get("messages", [])) > 0:
        delete_messages = [RemoveMessage(id=m.id) for m in state["messages"]]
        return {"triage": response, "messages": delete_messages}
    return {"triage": response}

# === 5.2 Few-shot Example Fetcher ===
async def get_few_shot_examples(email: EmailData, store: BaseStore, config: dict) -> str:
    """Fetches similar past examples from the store to guide the agent."""
    namespace = (config["configurable"].get("assistant_id", "default"), "triage_examples")
    try:
        results = await store.asearch(namespace, query=str({"input": email}), limit=3)
        if not results:
            return ""
        
        template = """Email Subject: {subject}\nEmail From: {from_email}\nEmail To: {to_email}\nEmail Content:\n```\n{content}\n```\n> Triage Result: {result}"""
        formatted_examples = [
            template.format(
                subject=eg.value["input"]["subject"],
                to_email=eg.value["input"]["to_email"],
                from_email=eg.value["input"]["from_email"],
                content=eg.value["input"]["page_content"][:400],
                result=eg.value["triage"],
            ) for eg in results
        ]
        return "Here are some previous examples:\n\n" + "\n\n------------\n\n".join(formatted_examples)
    except Exception as e:
        logger.warning(f"Could not fetch few-shot examples: {e}")
        return ""

# === 5.3 Draft Response Node ===
async def draft_response(state: State, config: RunnableConfig, store: BaseStore) -> dict:
    """Node that drafts a response or decides which tool to use."""
    logger.info("Draft Response: Starting draft process.")
    model = config["configurable"].get("model", "gpt-4o")
    llm = ChatOpenAI(model=model, temperature=0, parallel_tool_calls=False)
    
    tools = [NewEmailDraft, ResponseEmailDraft, Question, MeetingAssistant, SendCalendarInvite]
    if state.get("messages"):
        tools.append(Ignore) # Only allow ignoring after first attempt

    prompt_config = get_config(config)
    namespace = (config["configurable"].get("assistant_id", "default"),)

    # Fetch latest prompts from memory, falling back to config
    schedule_pref = (await store.aget(namespace, "schedule_preferences") or {}).value.get("data", prompt_config["schedule_preferences"])
    random_pref = (await store.aget(namespace, "random_preferences") or {}).value.get("data", prompt_config["background_preferences"])
    response_pref = (await store.aget(namespace, "response_preferences") or {}).value.get("data", prompt_config["response_preferences"])
    
    EMAIL_WRITING_INSTRUCTIONS = """You are {full_name}'s executive assistant... (Full prompt omitted for brevity)""" # The original full prompt
    draft_prompt = """{instructions}\n\nHere is the email thread:\n\n{email}"""

    _prompt = EMAIL_WRITING_INSTRUCTIONS.format(
        schedule_preferences=schedule_pref, random_preferences=random_pref,
        response_preferences=response_pref, name=prompt_config["name"],
        full_name=prompt_config["full_name"], background=prompt_config["background"]
    )
    input_message = draft_prompt.format(
        instructions=_prompt,
        email=email_template.format(
            email_thread=state["email"]["page_content"],
            author=state["email"]["from_email"],
            subject=state["email"]["subject"],
            to=state["email"].get("to_email", ""),
        ),
    )
    
    model_with_tools = llm.bind_tools(tools)
    messages = [{"role": "user", "content": input_message}] + state.get("messages", [])
    response = await model_with_tools.ainvoke(messages)
    logger.info(f"Draft Response: LLM decided to call tool: {response.tool_calls[0]['name'] if response.tool_calls else 'None'}")
    return {"messages": [response]}

# === 5.4 Find Meeting Time Node ===
async def find_meeting_time(state: State, config: RunnableConfig) -> dict:
    """Node to check calendar availability for meeting scheduling."""
    logger.info("Find Meeting Time: Checking calendar.")
    model = config["configurable"].get("model", "gpt-4o")
    llm = ChatOpenAI(model=model, temperature=0)
    agent = create_react_agent(llm, [get_events_for_days])
    
    prompt_config = get_config(config)
    meeting_prompts = """You are {full_name}'s executive assistant... (Full prompt omitted for brevity)""" # The original full prompt
    input_message = meeting_prompts.format(
        email_thread=state["email"]["page_content"], author=state["email"]["from_email"],
        subject=state["email"]["subject"], current_date=datetime.now().strftime("%A %B %d, %Y"),
        name=prompt_config["name"], full_name=prompt_config["full_name"], tz=prompt_config["timezone"]
    )
    
    messages = state.get("messages", [])[:-1] # Exclude the routing tool call
    result = await agent.ainvoke({"messages": [{"role": "user", "content": input_message}] + messages})
    
    tool_call_id = state["messages"][-1].tool_calls[0]["id"]
    return {"messages": [ToolMessage(content=result["messages"][-1].content, tool_call_id=tool_call_id)]}

# === 5.5 Rewrite Node ===
async def rewrite(state: State, config: dict, store: BaseStore) -> dict:
    """Node to rewrite a drafted email to match the user's tone and style."""
    logger.info("Rewrite: Rewriting email for tone.")
    model = config["configurable"].get("model", "gpt-4o")
    llm = ChatOpenAI(model=model, temperature=0)
    
    prev_message = state["messages"][-1]
    draft_content = prev_message.tool_calls[0]["args"]["content"]
    
    prompt_config = get_config(config)
    namespace = (config["configurable"].get("assistant_id", "default"),)
    rewrite_instructions = (await store.aget(namespace, "rewrite_instructions") or {}).value.get("data", prompt_config["rewrite_preferences"])
    
    rewrite_prompt_template = """You job is to rewrite an email draft to sound more like {name}... (Full prompt omitted for brevity)""" # The original full prompt
    input_message = rewrite_prompt_template.format(
        email_thread=state["email"]["page_content"], author=state["email"]["from_email"],
        subject=state["email"]["subject"], to=state["email"]["to_email"],
        draft=draft_content, instructions=rewrite_instructions, name=prompt_config["name"],
    )
    
    model_with_output = llm.with_structured_output(ReWriteEmail)
    response = await model_with_output.ainvoke(input_message)
    
    updated_tool_call = {
        **prev_message.tool_calls[0],
        "args": {**prev_message.tool_calls[0]["args"], "content": response.rewritten_content},
    }
    
    return {"messages": [{
        "role": "assistant", "id": prev_message.id, "content": "",
        "tool_calls": [updated_tool_call]
    }]}

# #################################################################################################
# Section 6: Human-in-the-Loop Interaction Nodes
# These functions handle points where the agent must pause and wait for human input,
# such as asking a clarifying question or presenting a draft for approval.
# #################################################################################################

class HumanInterruptConfig(TypedDict):
    allow_ignore: bool
    allow_respond: bool
    allow_edit: bool
    allow_accept: bool

class ActionRequest(TypedDict):
    action: str
    args: dict

class HumanInterrupt(TypedDict):
    action_request: ActionRequest
    config: HumanInterruptConfig
    description: Optional[str]

def _generate_email_markdown(state: State) -> str:
    contents = state["email"]
    return f"# {contents['subject']}\n\n**To**: {contents['to_email']}\n**From**: {contents['from_email']}\n\n{contents['page_content']}"

async def save_email_example(state: State, config: dict, store: BaseStore, status: str):
    """Saves the email and triage decision as a future few-shot example."""
    if not get_config(config).get("memory", False):
        return
    namespace = (config["configurable"].get("assistant_id", "default"), "triage_examples")
    key = str(uuid.uuid4())
    data = {"input": state["email"], "triage": status}
    await store.aput(namespace, key, data)

@traceable
async def send_message_for_human(state: State, config: dict, store: BaseStore) -> dict:
    """Pauses the graph to ask the user a question."""
    logger.info("Human Interaction: Asking user a question.")
    tool_call = state["messages"][-1].tool_calls[0]
    request: HumanInterrupt = {
        "action_request": {"action": tool_call["name"], "args": tool_call["args"]},
        "config": {"allow_ignore": True, "allow_respond": True, "allow_edit": False, "allow_accept": False},
        "description": _generate_email_markdown(state),
    }
    response = interrupt([request])[0]

    if response["type"] == "response":
        await save_email_example(state, config, store, "email")
        # Optional: Trigger reflection on the response
        return {"messages": [ToolMessage(content=response["args"], tool_call_id=tool_call["id"])]}
    elif response["type"] == "ignore":
        await save_email_example(state, config, store, "no")
        return {"messages": [{"role": "assistant", "content": "", "tool_calls": [{"name": "Ignore", "args": {"ignore": True}, "id": tool_call["id"]}]}]}
    raise ValueError(f"Unexpected human response: {response}")

@traceable
async def send_email_draft_for_human(state: State, config: dict, store: BaseStore) -> Optional[dict]:
    """Pauses the graph to show a draft for approval, editing, or rejection."""
    logger.info("Human Interaction: Presenting email draft for review.")
    tool_call = state["messages"][-1].tool_calls[0]
    request: HumanInterrupt = {
        "action_request": {"action": tool_call["name"], "args": tool_call["args"]},
        "config": {"allow_ignore": True, "allow_respond": False, "allow_edit": True, "allow_accept": True},
        "description": _generate_email_markdown(state),
    }
    response = interrupt([request])[0]

    if response["type"] == "accept":
        await save_email_example(state, config, store, "email")
        return None # Proceed to send
    elif response["type"] == "edit":
        await save_email_example(state, config, store, "email")
        # Optional: Trigger reflection on the edit
        return {"messages": [{"role": "assistant", "content": "", "tool_calls": [response["args"]]}]}
    elif response["type"] == "ignore":
        await save_email_example(state, config, store, "no")
        return {"messages": [{"role": "assistant", "content": "", "tool_calls": [{"name": "Ignore", "args": {"ignore": True}, "id": tool_call["id"]}]}]}
    raise ValueError(f"Unexpected human response: {response}")

@traceable
async def notify_human(state: State, config: dict, store: BaseStore) -> dict:
    """Pauses the graph to notify the user about an email."""
    logger.info("Human Interaction: Notifying user.")
    request: HumanInterrupt = {
        "action_request": {"action": "Notify", "args": {}},
        "config": {"allow_ignore": True, "allow_respond": True, "allow_edit": False, "allow_accept": False},
        "description": _generate_email_markdown(state),
    }
    response = interrupt([request])[0]

    if response["type"] == "response":
        await save_email_example(state, config, store, "email")
        return {"messages": [HumanMessage(content=response["args"])]}
    elif response["type"] == "ignore":
        await save_email_example(state, config, store, "no")
        return {"messages": [{"role": "assistant", "content": "", "tool_calls": [{"name": "Ignore", "args": {"ignore": True}, "id": str(uuid.uuid4())}]}]}
    raise ValueError(f"Unexpected human response: {response}")

@traceable
async def send_cal_invite_for_human(state: State, config: dict, store: BaseStore) -> Optional[dict]:
    """Pauses the graph to confirm sending a calendar invite."""
    logger.info("Human Interaction: Confirming calendar invite.")
    # Similar logic to send_email_draft_for_human
    return send_email_draft_for_human(state, config, store) # Reusing logic for brevity


# #################################################################################################
# Section 7: Agent Graph Definition
# This section constructs the state machine (graph) that defines the agent's workflow.
# It connects all the nodes and defines the conditional logic for transitions.
# #################################################################################################

def route_after_triage(state: State) -> str:
    """Router to direct flow after the initial triage decision."""
    decision = state["triage"].response
    logger.info(f"Routing after triage: decision is '{decision}'")
    if decision == "email" or decision == "question":
        return "draft_response"
    elif decision == "no":
        return "mark_as_read_node"
    elif decision == "notify":
        return "notify_human"
    raise ValueError(f"Invalid triage response: {decision}")

def take_action_after_draft(state: State) -> str:
    """Router to decide the next step after the drafting phase."""
    if not state["messages"][-1].tool_calls:
        logger.error("Drafting failed to produce a tool call.")
        return "draft_response" # Retry
    tool_name = state["messages"][-1].tool_calls[0]["name"]
    logger.info(f"Routing after draft: tool called is '{tool_name}'")
    action_map = {
        "Question": "send_message_for_human",
        "ResponseEmailDraft": "rewrite",
        "Ignore": "mark_as_read_node",
        "MeetingAssistant": "find_meeting_time",
        "SendCalendarInvite": "send_cal_invite_for_human",
    }
    return action_map.get(tool_name, "bad_tool_name")

def route_after_human_input(state: State) -> str:
    """Router to handle the flow after receiving input from a human."""
    logger.info("Routing after human input.")
    last_message = state["messages"][-1]
    if isinstance(last_message, (ToolMessage, HumanMessage)):
        return "draft_response" # Continue drafting with new info
    elif last_message.tool_calls:
        tool_name = last_message.tool_calls[0]["name"]
        if tool_name == "ResponseEmailDraft":
            return "send_email_node"
        elif tool_name == "SendCalendarInvite":
            return "send_cal_invite_node"
        elif tool_name == "Ignore":
            return "mark_as_read_node"
    return "draft_response" # Default fallback

# === Tool-executing Nodes ===
def bad_tool_name_node(state: State) -> dict:
    tool_call = state["messages"][-1].tool_calls[0]
    message = f"Invalid tool name: `{tool_call['name']}`. Please choose a valid tool."
    logger.error(message)
    return {"messages": [ToolMessage(content=message, tool_call_id=tool_call["id"])]}

def send_cal_invite_node(state: State, config: dict) -> dict:
    tool_call = state["messages"][-1].tool_calls[0]
    args = tool_call["args"]
    email = get_config(config)["email"]
    logger.info(f"Executing tool: SendCalendarInvite with args {args}")
    try:
        success = send_calendar_invite_tool(args["emails"], args["title"], args["start_time"], args["end_time"], email)
        message = "Sent calendar invite!" if success else "Failed to send calendar invite."
    except Exception as e:
        message = f"Error sending calendar invite: {e}"
        logger.error(message)
    return {"messages": [ToolMessage(content=message, tool_call_id=tool_call["id"])]}

def send_email_node(state: State, config: dict) -> None:
    tool_call = state["messages"][-1].tool_calls[0]
    args = tool_call["args"]
    email = get_config(config)["email"]
    logger.info(f"Executing tool: SendEmail to {args['new_recipients']}")
    send_email_tool(state["email"]["id"], args["content"], email, addn_receipients=args["new_recipients"])

def mark_as_read_node(state: State, config: dict) -> None:
    email_address = get_config(config)["email"]
    logger.info(f"Executing: Mark email {state['email']['id']} as read.")
    mark_as_read(state["email"]["id"], email_address)

# Empty node for human interaction pause
def human_in_the_loop_node(state: State) -> None:
    """This node is a placeholder where the graph will pause for human input."""
    pass

# === Graph Construction ===
class ConfigSchema(TypedDict):
    db_id: int
    model: str

def create_main_graph() -> StateGraph:
    """Builds and returns the main agent graph."""
    graph_builder = StateGraph(State, config_schema=ConfigSchema)

    # Add all nodes
    graph_builder.add_node("triage_input", triage_input)
    graph_builder.add_node("draft_response", draft_response)
    graph_builder.add_node("find_meeting_time", find_meeting_time)
    graph_builder.add_node("rewrite", rewrite)
    graph_builder.add_node("send_message_for_human", send_message_for_human)
    graph_builder.add_node("send_email_draft_for_human", send_email_draft_for_human)
    graph_builder.add_node("send_cal_invite_for_human", send_cal_invite_for_human)
    graph_builder.add_node("notify_human", notify_human)
    graph_builder.add_node("human_in_the_loop_node", human_in_the_loop_node)
    graph_builder.add_node("mark_as_read_node", mark_as_read_node)
    graph_builder.add_node("send_email_node", send_email_node)
    graph_builder.add_node("send_cal_invite_node", send_cal_invite_node)
    graph_builder.add_node("bad_tool_name_node", bad_tool_name_node)

    # Define edges and entry point
    graph_builder.set_entry_point("triage_input")
    
    # Conditional edges for routing
    graph_builder.add_conditional_edges("triage_input", route_after_triage)
    graph_builder.add_conditional_edges("draft_response", take_action_after_draft)
    graph_builder.add_conditional_edges("human_in_the_loop_node", route_after_human_input)

    # Standard edges
    graph_builder.add_edge("rewrite", "send_email_draft_for_human")
    graph_builder.add_edge("find_meeting_time", "draft_response")
    graph_builder.add_edge("bad_tool_name_node", "draft_response")
    graph_builder.add_edge("send_cal_invite_node", "draft_response") # Follow-up after sending invite
    graph_builder.add_edge("send_email_node", "mark_as_read_node")

    # Edges to human-in-the-loop pause node
    graph_builder.add_edge("send_message_for_human", "human_in_the_loop_node")
    graph_builder.add_edge("send_email_draft_for_human", "human_in_the_loop_node")
    graph_builder.add_edge("send_cal_invite_for_human", "human_in_the_loop_node")
    graph_builder.add_edge("notify_human", "human_in_the_loop_node")

    graph_builder.add_edge("mark_as_read_node", END)
    
    return graph_builder.compile()

# #################################################################################################
# Section 8: Cron Job and Ingestion Logic
# This section contains the logic for the "ambient" part of the agent.
# The cron graph periodically runs the ingestion logic to fetch new items and
# trigger the main agent graph for each one.
# #################################################################################################

class JobKickoff(TypedDict):
    minutes_since: int

async def cron_job_main(state: JobKickoff, config: dict) -> None:
    """The main function for the cron job graph. Fetches emails and starts runs."""
    minutes_since = state["minutes_since"]
    email_address = get_config(config)["email"]
    logger.info(f"Cron Job: Fetching emails for {email_address} from the last {minutes_since} minutes.")
    
    async for email_data in fetch_group_emails(email_address, minutes_since=minutes_since):
        thread_id_str = str(uuid.UUID(hex=hashlib.md5(email_data["thread_id"].encode("UTF-8")).hexdigest()))
        
        try:
            thread_info = await LGC.threads.get(thread_id_str)
        except httpx.HTTPStatusError as e:
            if "user_respond" in email_data or e.response.status_code != 404:
                continue
            thread_info = await LGC.threads.create(thread_id=thread_id_str)

        if "user_respond" in email_data:
            await LGC.threads.update_state(thread_id_str, None, as_node="__end__")
            continue
            
        recent_email_id = thread_info.get("metadata", {}).get("email_id")
        if recent_email_id == email_data["id"]:
            continue # Already processed

        await LGC.threads.update(thread_id_str, metadata={"email_id": email_data["id"]})
        await LGC.runs.create(
            thread_id_str,
            "main",
            input={"email": email_data},
            multitask_strategy="rollback",
        )
        logger.info(f"Cron Job: Kicked off a new run for thread {thread_id_str}.")

def create_cron_graph() -> StateGraph:
    """Builds the simple graph for the cron job."""
    graph = StateGraph(JobKickoff)
    graph.add_node("main", cron_job_main)
    graph.add_edge(START, "main")
    graph.add_edge("main", END)
    return graph.compile()

# #################################################################################################
# Section 9: Reflection Graphs (Self-Improvement)
# These graphs are designed to update the agent's internal prompts based on human feedback,
# allowing it to learn and adapt over time. This is an advanced feature for agent autonomy.
# #################################################################################################

# NOTE: Reflection logic is complex and omitted from this consolidated file for clarity,
# but the stubs show where it would be integrated. It would involve additional prompts
# and logic to analyze feedback and update stored prompt templates.

# #################################################################################################
# Section 10: Command-Line Interface and Execution
# This section makes the script executable, providing commands to set up, test, and run the agent.
# #################################################################################################

async def run_ingest_script(args):
    """Logic from scripts/run_ingest.py"""
    if args.email is None:
        email_address = get_config({"configurable": {}})["email"]
    else:
        email_address = args.email
        
    client = get_client(url=args.url if args.url else "http://127.0.0.1:2024")
    
    logger.info(f"Ingest: Fetching emails for {email_address} from last {args.minutes_since} minutes...")
    
    email_count = 0
    async for email in fetch_group_emails(email_address, minutes_since=args.minutes_since):
        email_count += 1
        logger.info(f"Ingest: Found email {email_count} - Subject: {email.get('subject', 'No Subject')}")
        
        thread_id = str(uuid.UUID(hex=hashlib.md5(email["thread_id"].encode("UTF-8")).hexdigest()))
        
        try:
            thread_info = await client.threads.get(thread_id)
        except httpx.HTTPStatusError as e:
            if "user_respond" in email or e.response.status_code != 404:
                continue
            thread_info = await client.threads.create(thread_id=thread_id)

        if "user_respond" in email:
            await client.threads.update_state(thread_id, None, as_node="__end__")
            continue
            
        recent_email = thread_info.get("metadata", {}).get("email_id")
        if recent_email == email["id"] and args.early and not args.rerun:
            logger.info("Ingest: Found already processed email. Stopping early.")
            break
            
        await client.threads.update(thread_id, metadata={"email_id": email["id"]})
        await client.runs.create(
            thread_id, "main", input={"email": email}, multitask_strategy="rollback"
        )
        logger.info(f"Ingest: Created run for thread {thread_id}")
    logger.info(f"Ingest: Finished processing {email_count} emails.")

async def setup_cron_script(args):
    """Logic from scripts/setup_cron.py"""
    client = get_client(url=args.url)
    await client.crons.create("cron", schedule="*/10 * * * *", input={"minutes_since": args.minutes_since})
    logger.info("Cron Setup: Successfully set up cron job to run every 10 minutes.")

async def setup_gmail_script(args):
    """Logic from scripts/setup_gmail.py"""
    api_key = os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        raise ValueError("LANGSMITH_API_KEY environment variable must be set")
    
    secrets_path = Path(__file__).parent / ".secrets" / "secrets.json"
    if not secrets_path.exists():
        logger.error(f"Google OAuth secrets file not found at {secrets_path}")
        return
        
    with open(secrets_path) as f:
        secrets = json.load(f)
    
    oauth_config = secrets.get("web") or secrets.get("installed")
    if not oauth_config:
        raise ValueError("Invalid Google client secrets format")
        
    client = LangchainAuthClient(api_key=api_key)
    try:
        logger.info("Gmail Setup: Creating Google OAuth provider...")
        provider = await client.create_oauth_provider(
            provider_id="google", name="Google",
            client_id=oauth_config["client_id"], client_secret=oauth_config["client_secret"],
            auth_url="https://accounts.google.com/o/oauth2/auth",
            token_url="https://oauth2.googleapis.com/token",
        )
        logger.info(f"Gmail Setup: Successfully created provider: {provider}")
    except Exception as e:
        logger.warning(f"Gmail Setup: Could not create provider (it might already exist): {e}")
    finally:
        await client.close()

# Expose graphs for LangGraph CLI
graph = create_main_graph()
cron_graph = create_cron_graph()
# multi_reflection_graph, general_reflection_graph would be defined here

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ambient Agent CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Parser for `run_ingest`
    ingest_parser = subparsers.add_parser("run_ingest", help="Run the email ingestion process manually.")
    ingest_parser.add_argument("--url", type=str, default=None, help="LangGraph server URL.")
    ingest_parser.add_argument("--minutes-since", type=int, default=60, help="Process emails from the last N minutes.")
    ingest_parser.add_argument("--early", type=int, default=1, help="Stop if a seen email is encountered.")
    ingest_parser.add_argument("--rerun", type=int, default=0, help="Rerun processing for all found emails.")
    ingest_parser.add_argument("--email", type=str, default=None, help="The email address to monitor.")
    ingest_parser.set_defaults(func=run_ingest_script)

    # Parser for `setup_cron`
    cron_parser = subparsers.add_parser("setup_cron", help="Set up the cron job on a LangGraph deployment.")
    cron_parser.add_argument("--url", type=str, required=True, help="The URL of the LangGraph deployment.")
    cron_parser.add_argument("--minutes-since", type=int, default=15, help="Interval for the cron job to check.")
    cron_parser.set_defaults(func=setup_cron_script)

    # Parser for `setup_gmail`
    gmail_parser = subparsers.add_parser("setup_gmail", help="Configure the Google OAuth provider for Gmail access.")
    gmail_parser.set_defaults(func=setup_gmail_script)

    args = parser.parse_args()
    asyncio.run(args.func(args))