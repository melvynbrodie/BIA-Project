# BIA Project - AI Business Analyst

![BIA Project Banner](frontend/public/window.svg)

## Overview
The **BIA Project** is an AI-powered financial analysis tool designed to help users understand company performance through advanced metrics, automated report analysis, and interactive chat.

Built with:
- **Frontend**: Next.js 14, TailwindCSS, Framer Motion
- **Backend**: FastAPI, Python, LangChain
- **AI Engine**: Google Gemini Pro (via API)
- **Database**: PostgreSQL with `pgvector` for RAG (Retrieval Augmented Generation)

## Features
- 📊 **Real-time Metrics**: Live stock data, market cap, and P/E ratios.
- 🤖 **AI Chat Analyst**: Chat with annual reports using RAG technology.
- 📄 **PDF Analysis**: Upload Annual Reports (PDF) and get instant summaries.
- 🚀 **Modern UI**: Dark-themed, glassmorphism design for a premium feel.

## Local Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Deployment
- **Frontend**: Deployed on [Vercel](https://vercel.com)
- **Backend**: Hosted on [Render](https://render.com)

## License
MIT License
