# VeriShield AI Project Structure

## Overview
VeriShield AI is an agentic deepfake defense system for enterprise financial workflows. The system uses multiple AI agents to detect deepfakes in real-time and autonomously trigger actions based on risk scores.

## Tech Stack
- **Backend**: Python/FastAPI
- **AI Agents**:
  - Visual Agent: Azure AI Vision SDK
  - Acoustic Agent: Azure AI Speech SDK
  - Reasoning Agent: Azure OpenAI (GPT-4o)
- **Autonomous Action**: Azure Functions
- **Frontend**: React/Tailwind

## Folder Structure

```
VeriShieldAI/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models/
│   │   ├── routes/
│   │   ├── services/
│   │   └── utils/
│   ├── requirements.txt
│   └── Dockerfile
├── agents/
│   ├── visual_agent/
│   │   ├── face_liveness.py
│   │   ├── pixel_artifact_analysis.py
│   │   └── config.py
│   ├── acoustic_agent/
│   │   ├── frequency_analysis.py
│   │   └── config.py
│   ├── reasoning_agent/
│   │   ├── risk_correlation.py
│   │   └── config.py
│   └── azure_orchestrator.py
├── azure_functions/
│   ├── soft_lock_trigger/
│   │   ├── __init__.py
│   │   ├── function.json
│   │   └── requirements.txt
│   └── host.json
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── styles/
│   │   ├── App.js
│   │   ├── index.js
│   │   └── setupProxy.js
│   ├── package.json
│   └── tailwind.config.js
├── config/
│   ├── .env.template
│   └── settings.py
├── scripts/
│   ├── setup.sh
│   └── deploy.sh
├── tests/
│   ├── unit/
│   └── integration/
├── .gitignore
├── README.md
└── requirements.txt

## Key Components

### Backend (FastAPI)
- **main.py**: Entry point for the FastAPI application.
- **config.py**: Configuration settings for the backend.
- **models/**: Data models and schemas.
- **routes/**: API endpoints.
- **services/**: Business logic and services.
- **utils/**: Utility functions and helpers.

### AI Agents
- **visual_agent/**: Uses Azure AI Vision SDK for face liveness detection and pixel artifact analysis.
- **acoustic_agent/**: Uses Azure AI Speech SDK to detect frequency anomalies in cloned voices.
- **reasoning_agent/**: Uses Azure OpenAI (GPT-4o) to correlate risk scores from both agents.
- **azure_orchestrator.py**: Orchestrates the interaction between agents and the backend.

### Azure Functions
- **soft_lock_trigger/**: Azure Function that triggers a "Soft Lock" on a transaction if the combined risk score is >85%.

### Frontend (React/Tailwind)
- **components/**: Reusable UI components.
- **pages/**: Application pages.
- **styles/**: CSS and Tailwind configuration.
- **App.js**: Main application component.
- **index.js**: Entry point for the React application.
- **setupProxy.js**: Proxy configuration for API calls.

### Configuration
- **.env.template**: Template for environment variables.
- **settings.py**: Application settings and configurations.

### Scripts
- **setup.sh**: Script to set up the development environment.
- **deploy.sh**: Script to deploy the application.

### Tests
- **unit/**: Unit tests.
- **integration/**: Integration tests.

## Next Steps
1. Create the folder structure as defined above.
2. Implement the `azure_orchestrator.py` logic.
3. Set up configuration files for environment variables.
4. Implement the backend and frontend components.
5. Develop and test the AI agents.
6. Deploy the Azure Functions.
