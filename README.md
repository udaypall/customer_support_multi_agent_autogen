# 🤖 Customer Support Multi-Agent Chat BoT using AutoGen

## 📌 Project Overview

This project is an AI-powered Customer Support Chatbot built using **Microsoft AutoGen, OpenAI and Streamlit**.

The application uses four AI agents: one Manager Agent and three specialized department agents (IT, HR and Finance).

The Manager Agent analyzes customer questions and automatically routes them to the appropriate department. The selected department agent provides relevant answers using company policy PDF documents, employee FAQs and conversation context.

## 🔗 GitHub Repository

[Customer Support Multi-Agent – GitHub Repository](https://github.com/udaypall/customer_support_multi_agent_autogen.git)

## 🎯 Project Objectives

- Build a multi-agent customer support system using AutoGen.
- Implement intelligent department-based question routing.
- Create specialized IT, HR and Finance agents.
- Integrate OpenAI for AI-powered responses.
- Retrieve information from company policy PDFs.
- Include employee FAQs and conversation memory.
- Develop an interactive Streamlit interface.

## 🏗️ System Architecture

| Agent | Responsibility |
|---|---|
| Manager Agent | Analyzes customer questions and routes them to the correct department. |
| IT Agent | Handles technical support queries. |
| HR Agent | Handles employee-related queries. |
| Finance Agent | Handles financial and reimbursement queries. |

## 🛠️ Technologies Used

- Python
- Microsoft AutoGen
- OpenAI GPT-4o-mini
- Streamlit
- PyPDF
- Python-dotenv

## 📚 Knowledge Base

The application uses three department-specific sample policy PDFs:

- IT_Company_Policy.pdf
- HR_Company_Policy.pdf
- Finance_Company_Policy.pdf

Employee FAQs are also integrated into the application.

## ✨ Key Features

- Four-agent architecture.
- Intelligent department routing.
- Department-specific AI responses.
- PDF policy document extraction.
- Employee FAQ integration.
- Conversation memory.
- PDF source references.
- Interactive Streamlit chat interface.
- Clear conversation functionality.

## ⚙️ Installation and Setup

### 1. Clone Repository

```cmd
git clone https://github.com/udaypall/customer_support_multi_agent_autogen.git
cd customer_support_multi_agent_autogen
```

### 2. Create Virtual Environment

```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```cmd
pip install -r requirements.txt
```

### 4. Configure OpenAI API Key

Create a `.env` file:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 5. Run Application

```cmd
python -m streamlit run app.py
```

Open http://localhost:8501 in your browser.

## 🚀 Project Outcome

Successfully demonstrates how multiple AI agents can collaborate to provide intelligent customer support through automated department routing, policy-based knowledge extraction and contextual AI-generated responses.

**Developed using Python, Microsoft AutoGen, OpenAI and Streamlit.**