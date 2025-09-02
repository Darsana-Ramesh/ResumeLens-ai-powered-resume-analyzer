# ResumeLens

ResumeLens is a web-based platform designed to help candidates evaluate how well their resumes match job descriptions and assist recruiters in shortlisting candidates efficiently.

Built with Flask, Google Gemini API, and Tailwind UI, the platform provides real-time skill extraction, match scoring, gap analysis, job recommendations, and AI-generated cover letters.

## Features

### For Candidates
- Upload resume (PDF) and paste a job description.
- Get an instant Match Score (percentage of skills matched).
- View missing skills at a glance.
- Discover recommended job roles based on your skills.
- Generate AI-powered personalized cover letters.

### For Recruiters
- Upload multiple resumes (PDFs) along with a job description.
- AI extracts candidate details (name, email, phone, skills).
- Visual bar chart comparing Match Scores.
- Individual pie charts for each candidate’s skill match.
- Breakdown of missing skills per candidate.
- Sorted ranking of candidates by match percentage.

## Tech Stack

- **Backend:** Flask (Python)  
- **AI:** Google Gemini API (Generative AI for skills extraction & cover letters)  
- **Parsing:** PyPDF2 (for extracting text from resumes)  
- **Visualization:** Matplotlib (bar & pie charts, Base64 embedded)  
- **Frontend:** TailwindCSS + Chart.js (responsive, modern UI)  
- **Environment:** python-dotenv for API key management

## Prerequisites

- Python 3.x installed on your system
- pip installed

## Installation & Setup (Without Virtual Environment)

### 1. Install Dependencies Globally

Open a terminal or command prompt and run:

```bash
pip install Flask matplotlib PyPDF2 python-dotenv requests

### 1. Install Dependencies Globally
