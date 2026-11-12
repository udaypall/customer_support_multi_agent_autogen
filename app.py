
import asyncio
import os
import re
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient


# ==================================================
# 1. CONFIGURATION
# ==================================================

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-4o-mini"

BASE_DIR = Path(__file__).parent
PDF_FOLDER = BASE_DIR / "knowledge_base"

DEPARTMENTS = ["IT", "HR", "FINANCE"]


# ==================================================
# 2. EMPLOYEE FAQ KNOWLEDGE BASE
# ==================================================

FAQS = {

    "IT": """
    Q: How do I reset my password?
    A: Follow the approved company password reset process.
       Contact IT if you cannot access the reset facility.

    Q: How do I connect to VPN?
    A: Connect to the internet, open the company VPN client,
       sign in using your authorized company credentials,
       and complete MFA if required.

    Q: My laptop is slow. What should I do?
    A: Save your work, restart the laptop, close unnecessary
       applications, and contact IT if the problem continues.

    Q: How do I report a phishing email?
    A: Do not click suspicious links. Report the message
       to the IT team.
    """,

    "HR": """
    Q: How do I apply for leave?
    A: Submit your leave request through the approved
       company HR system or process.

    Q: How do I correct attendance?
    A: Contact your manager or HR and provide the
       relevant date and attendance details.

    Q: How do I ask about employee benefits?
    A: Contact HR for current benefit eligibility
       and official company information.

    Q: What happens during onboarding?
    A: Complete the onboarding steps and documentation
       communicated by the HR team.
    """,

    "FINANCE": """
    Q: How do I claim expenses?
    A: Submit your claim through the approved expense
       process with the required supporting receipts.

    Q: What documents are needed for reimbursement?
    A: Provide the business purpose, transaction date,
       amount, and itemized receipt where required.

    Q: How do I check invoice payment status?
    A: Contact Finance with the invoice number,
       supplier name, and relevant purchase reference.

    Q: How do I ask about payroll?
    A: Contact authorized Finance or Payroll personnel
       through approved company channels.
    """
}


# ==================================================
# 3. EXTRACT TEXT FROM DEPARTMENT PDF FILES
# ==================================================

@st.cache_data
def load_policy_documents():

    documents = {
        "IT": [],
        "HR": [],
        "FINANCE": []
    }

    if not PDF_FOLDER.exists():
        return documents

    department_files = {
        "IT": "IT",
        "HR": "HR",
        "FINANCE": "Finance"
    }

    for department, prefix in department_files.items():

        pdf_files = list(
            PDF_FOLDER.glob(f"{prefix}*.pdf")
        )

        for pdf_file in pdf_files:

            try:

                reader = PdfReader(str(pdf_file))

                for page_number, page in enumerate(reader.pages, start=1):

                    text = page.extract_text()

                    if text and text.strip():

                        documents[department].append({
                            "filename": pdf_file.name,
                            "page": page_number,
                            "text": text
                        })

            except Exception as error:

                print(
                    f"Could not read {pdf_file.name}: {error}"
                )

    return documents


# ==================================================
# 4. RETRIEVE RELEVANT PDF CONTENT
# ==================================================

def retrieve_policy(question, department, documents):

    department_documents = documents.get(
        department, []
    )

    question_words = set(
        re.findall(r"\b[a-zA-Z]{3,}\b", question.lower())
    )

    results = []

    for document in department_documents:

        text = document["text"]

        text_words = set(
            re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        )

        score = len(question_words.intersection(text_words))

        if score > 0:

            results.append({
                "score": score,
                "filename": document["filename"],
                "page": document["page"],
                "text": text
            })

    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    # Select up to three relevant PDF pages
    selected_results = results[:3]

    if not selected_results:
        return "No directly matching policy information found.", []

    context = []

    sources = []

    for item in selected_results:

        context.append(
            f"""
            Source: {item['filename']}
            Page: {item['page']}

            Content:
            {item['text']}
            """
        )

        sources.append(
            f"{item['filename']} (Page {item['page']})"
        )

    return "\n\n".join(context), sources


# ==================================================
# 5. FORMAT PREVIOUS CONVERSATION
# ==================================================

def get_conversation_context(history):

    if not history:
        return "This is the beginning of the conversation."

    context = []

    for message in history[-10:]:

        role = message["role"].upper()

        context.append(
            f"{role}: {message['content']}"
        )

    return "\n".join(context)


# ==================================================
# 6. CREATE AND EXECUTE AUTOGEN AGENTS
# ==================================================

async def process_question(question, history, documents):

    model_client = OpenAIChatCompletionClient(
        model=MODEL_NAME,
        api_key=API_KEY
    )

    try:

        conversation_context = get_conversation_context(
            history
        )

        # ------------------------------------------
        # MANAGER AGENT
        # ------------------------------------------

        manager_agent = AssistantAgent(

            name="Manager_Agent",

            model_client=model_client,

            system_message="""
            You are the Customer Support Manager.

            Your responsibility is to route customer
            questions to the correct department.

            Available departments:

            IT:
            Technical support, computers, software,
            hardware, network, VPN, email and access.

            HR:
            Leave, attendance, employee policies,
            recruitment, benefits and onboarding.

            FINANCE:
            Salary, reimbursements, expenses,
            invoices, budgets and payments.

            Consider the conversation history when
            interpreting follow-up questions.

            Classify the LATEST customer question.

            Return ONLY one of these values:

            IT
            HR
            FINANCE

            Never return explanations or other text.
            """

        )

        manager_task = f"""
        Previous conversation:
        {conversation_context}

        Latest customer question:
        {question}

        Select the appropriate department.
        """

        manager_result = await manager_agent.run(
            task=manager_task
        )

        department = str(
            manager_result.messages[-1].content
        ).strip().upper()

        # Extract a valid department even if
        # the model adds extra formatting.
        match = re.search(
            r"\b(IT|HR|FINANCE)\b",
            department
        )

        if not match:

            return (
                "I could not identify the correct department. "
                "Please rephrase your question.",
                "Manager Agent",
                []
            )

        department = match.group(1)

        # ------------------------------------------
        # RETRIEVE DEPARTMENT KNOWLEDGE
        # ------------------------------------------

        policy_context, sources = retrieve_policy(
            question,
            department,
            documents
        )

        faq_context = FAQS.get(
            department,
            ""
        )

        # ------------------------------------------
        # SELECT DEPARTMENT AGENT
        # ------------------------------------------

        if department == "IT":

            selected_agent = AssistantAgent(

                name="IT_Agent",

                model_client=model_client,

                system_message="""
                You are an experienced IT support specialist.

                Handle technical questions related to:
                computers, software, hardware, internet,
                VPN, email, passwords and system access.

                Use the supplied company policy PDFs and
                employee FAQs as your primary knowledge.

                Do not invent company policies or technical
                actions that could compromise security.

                If the supplied knowledge does not contain
                the answer, clearly say that IT should
                confirm the details.

                Provide clear, practical answers.
                """
            )

            department_name = "IT Department"

        elif department == "HR":

            selected_agent = AssistantAgent(

                name="HR_Agent",

                model_client=model_client,

                system_message="""
                You are an experienced HR support specialist.

                Handle questions related to leave, attendance,
                employee benefits, onboarding, recruitment
                and workplace policies.

                Use the supplied company policy PDFs and
                employee FAQs as your primary knowledge.

                Never invent leave balances, employee
                information or company policies.

                If information is unavailable, direct the
                employee to HR for confirmation.

                Maintain a professional and helpful tone.
                """
            )

            department_name = "HR Department"

        else:

            selected_agent = AssistantAgent(

                name="Finance_Agent",

                model_client=model_client,

                system_message="""
                You are an experienced Finance support specialist.

                Handle questions related to salary, invoices,
                reimbursements, expenses, payments and budgets.

                Use the supplied company policy PDFs and
                employee FAQs as your primary knowledge.

                Never invent salary figures, payment dates,
                bank details or financial records.

                If information is unavailable, direct the
                employee to authorized Finance personnel.

                Maintain a professional and helpful tone.
                """
            )

            department_name = "Finance Department"

        # ------------------------------------------
        # SPECIALIST AGENT ANSWERS THE QUESTION
        # ------------------------------------------

        specialist_task = f"""
        CUSTOMER SUPPORT REQUEST

        Previous conversation:
        {conversation_context}

        Latest customer question:
        {question}

        DEPARTMENT:
        {department}

        EMPLOYEE FAQ KNOWLEDGE:
        {faq_context}

        RETRIEVED COMPANY POLICY PDF CONTENT:
        {policy_context}

        INSTRUCTIONS:

        1. Answer the latest customer question.
        2. Consider previous conversation for context.
        3. Use the supplied FAQs and PDF information.
        4. Do not invent company policies.
        5. If the answer is not available, say so clearly.
        6. Keep the response simple and professional.
        7. Mention relevant PDF source and page when available.
        """

        specialist_result = await selected_agent.run(
            task=specialist_task
        )

        answer = specialist_result.messages[-1].content

        return answer, department_name, sources

    finally:

        await model_client.close()


# ==================================================
# 7. STREAMLIT USER INTERFACE
# ==================================================

st.set_page_config(
    page_title="AI Customer Support",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 AI Customer Support")

st.caption(
    "Powered by AutoGen, OpenAI and Streamlit"
)

st.write(
    "Welcome! Ask questions about IT, HR or Finance. "
    "Our Manager Agent will connect you to the correct team."
)


# Check API key

if not API_KEY:

    st.error(
        "OpenAI API key not found. Please check your .env file."
    )

    st.stop()


# Load PDF documents

documents = load_policy_documents()

# Initialize conversation memory

if "messages" not in st.session_state:

    st.session_state.messages = []


# Sidebar

with st.sidebar:

    st.header("Customer Support")

    st.write("**Available departments**")

    st.write("💻 IT Team")
    st.write("👥 HR Team")
    st.write("💰 Finance Team")

    st.divider()

    st.subheader("Knowledge Base")

    for department in DEPARTMENTS:

        st.write(
            f"{department}: "
            f"{len(documents[department])} PDF pages loaded"
        )

    st.divider()

    st.write(
        f"Conversation messages: "
        f"{len(st.session_state.messages)}"
    )

    if st.button("Clear Conversation"):

        st.session_state.messages = []

        st.rerun()


# Display previous messages

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        if message.get("department"):

            st.caption(
                f"Department: {message['department']}"
            )

        st.markdown(message["content"])

        if message.get("sources"):

            with st.expander("View policy sources"):

                for source in message["sources"]:

                    st.write(f"📄 {source}")


# Customer input

if question := st.chat_input(
    "Ask your question..."
):

    # Preserve previous conversation before
    # adding the current question.

    previous_history = list(
        st.session_state.messages
    )

    # Display customer question

    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):

        st.markdown(question)

    # Process the question

    with st.chat_message("assistant"):

        with st.spinner(
            "Manager is selecting the right department..."
        ):

            try:

                answer, department, sources = asyncio.run(
                    process_question(
                        question,
                        previous_history,
                        documents
                    )
                )

                st.success(
                    f"Handled by: {department}"
                )

                st.markdown(answer)

                # Display policy sources

                if sources:

                    with st.expander("View policy sources"):

                        for source in sources:

                            st.write(f"📄 {source}")

                # Save conversation memory

                st.session_state.messages.append({

                    "role": "assistant",

                    "content": answer,

                    "department": department,

                    "sources": sources

                })

            except Exception as error:

                st.error(
                    f"Something went wrong: {error}"
                )
