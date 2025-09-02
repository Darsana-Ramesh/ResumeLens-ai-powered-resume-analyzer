from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import PyPDF2
import io
import os
import json
import base64
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# --- Backend Logic (Functions remain the same, adapted for Flask) ---
try:
    gemini_api_key = os.getenv("GOOGLE_API_KEY")
    if not gemini_api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")
    genai.configure(api_key=gemini_api_key)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"Error configuring Google Gemini API: {e}. Please ensure your API key is correctly set.")
    gemini_model = None

def extract_text_from_pdf(pdf_file):
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ''.join(page.extract_text() or "" for page in reader.pages)
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def extract_skills_from_text(text):
    if not gemini_model:
        return None
    try:
        # Prompt the model to only extract skills, not job titles or other text.
        prompt = f"""Extract a concise and precise list of technical skills, separated by commas, from the following text. Do not include job titles or non-technical skills.\n{text}"""
        response = gemini_model.generate_content(prompt)
        # Added a check to handle cases where the response is empty
        return response.text.strip() if response.text else None
    except Exception as e:
        print(f"Error extracting skills: {e}")
        return None

def recommend_jobs_from_skills(resume_skills):
    if not gemini_model:
        return None
    try:
        prompt = f"""
        Based on the provided skills, recommend suitable job roles categorized by experience level (e.g., 'junior', 'mid', 'senior').

        Skills: {resume_skills}

        Return JSON only, in this precise format:
        {{
          "junior": ["Job Title 1", "Job Title 2"],
          "mid": ["Job Title 3", "Job Title 4"],
          "senior": ["Job Title 5"]
        }}
        """

        response = gemini_model.generate_content(prompt)
        # Sanitize and parse the JSON response
        cleaned_response_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_response_text)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from Gemini response: {e}")
        return None
    except Exception as e:
        print(f"Error identifying missing skills and recommending jobs: {e}")
        return None

def calculate_match_score(resume_skills, job_skills):
    if not resume_skills or not job_skills:
        return 0
    resume_set = {s.strip().lower() for s in resume_skills.split(',') if s.strip()}
    job_set = {s.strip().lower() for s in job_skills.split(',') if s.strip()}
    matched = resume_set.intersection(job_set)
    return int((len(matched) / len(job_set)) * 100) if job_set else 0

def generate_cover_letter(resume_skills, job_desc):
    if not gemini_model:
        return "Cover letter generation is currently unavailable. Please check your API key."
    try:
        prompt = f"""Generate a concise cover letter highlighting the following skills for the given job description.

Resume Skills: {resume_skills}
Job Description: {job_desc}"""
        response = gemini_model.generate_content(prompt)
        return response.text if response.text else "Cover letter generation failed due to an API error."
    except Exception as e:
        print(f"Error generating cover letter: {e}")
        return "Cover letter generation failed due to an API error."


def generate_bar_chart_base64(candidate_names, match_scores):
    plt.figure(figsize=(10, 6))
    plt.bar(candidate_names, match_scores, color='#3B82F6')
    plt.xlabel("Candidates")
    plt.ylabel("Match Score (%)")
    plt.ylim(0, 100)
    plt.title("Candidate Match Score Comparison")

    buf = io.BytesIO()
    plt.savefig(buf, format='png', transparent=True)
    plt.close()
    buf.seek(0)

    return base64.b64encode(buf.getvalue()).decode('utf-8')

def extract_name_skills_and_contact(pdf_text):
    if not gemini_model:
        return None
    try:
        prompt = f"""
        From the following resume text, extract the candidate's name, a comma-separated list of their skills, their email address, and their phone number.
        Return the information as a JSON object with keys 'name', 'skills', 'email', and 'phone'.
        Text:
        {pdf_text}
        """
        response = gemini_model.generate_content(prompt)
        if not response or not response.text:
            print("Error: Gemini API returned an empty or invalid response.")
            return None
        cleaned_response_text = response.text.replace("```json", "").replace("```", "").strip()
        extracted_info = json.loads(cleaned_response_text)
        return extracted_info
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from Gemini response: {e}")
        return None
    except Exception as e:
        print(f"Error extracting info with Gemini: {e}")
        return None

def generate_pie_chart_base64(match_percentage):
    # Calculate sizes for matched and missing skills based on percentage
    matched_skills_size = match_percentage
    missing_skills_size = 100 - match_percentage

    # Data for the pie chart
    labels = 'Matched Skills', 'Missing Skills'
    sizes = [matched_skills_size, missing_skills_size]
    colors = ['#10B981', '#F43F5E']  # Green for matched, Red for missing
    explode = (0.1, 0) if matched_skills_size > 0 else (0, 0.1)

    # Increase the figure size to make the chart larger
    plt.figure(figsize=(6, 6))
    plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
            shadow=True, startangle=140, textprops={'fontsize': 12, 'color': 'white'}) # Adjusted font size
    plt.axis('equal')

    # Save chart to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', transparent=True)
    plt.close()
    buf.seek(0)

    # Encode the image to Base64
    pie_chart_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return pie_chart_base64

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'resume' not in request.files or 'job_desc' not in request.form:
        return jsonify({"error": "No file or job description provided."}), 400

    resume_file = request.files['resume']
    job_desc_text = request.form['job_desc']

    pdf_data = io.BytesIO(resume_file.read())
    pdf_text = extract_text_from_pdf(pdf_data)

    if not pdf_text:
        return jsonify({"error": "Failed to extract text from PDF."}), 500

    resume_skills_text = extract_skills_from_text(pdf_text)
    job_skills_text = extract_skills_from_text(job_desc_text)
    
    if not resume_skills_text or not job_skills_text:
        return jsonify({"error": "Failed to extract skills from text."}), 500

    # Convert skills to sets for accurate comparison
    resume_skills_set = {s.strip().lower() for s in resume_skills_text.split(',') if s.strip()}
    job_skills_set = {s.strip().lower() for s in job_skills_text.split(',') if s.strip()}

    # Calculate missing skills and match percentage programmatically
    missing_skills = list(job_skills_set - resume_skills_set)
    matched_skills = job_skills_set.intersection(resume_skills_set)
    match_percentage = int((len(matched_skills) / len(job_skills_set)) * 100) if job_skills_set else 0

    # Call the AI to get only job recommendations
    recommended_jobs = recommend_jobs_from_skills(resume_skills_text)

    if not recommended_jobs:
        return jsonify({"error": "Failed to get job recommendations from AI."}), 500

    return jsonify({
        "match_percentage": match_percentage,
        "missing_skills": missing_skills,
        "recommended_jobs": recommended_jobs,
        "resume_skills": resume_skills_text,
        "job_skills": job_skills_text
    })

@app.route('/generate-cover-letter', methods=['POST'])
def generate_cover_letter_route():
    data = request.json
    resume_skills = data.get('resume_skills')
    job_desc = data.get('job_desc')
    
    if not resume_skills or not job_desc:
        return jsonify({"error": "Resume skills or job description not provided."}), 400

    cover_letter = generate_cover_letter(resume_skills, job_desc)
    
    return jsonify({"cover_letter": cover_letter})

@app.route('/analyze-recruiter', methods=['POST'])
def analyze_recruiter():
    if 'resumes[]' not in request.files or 'job_desc' not in request.form:
        return jsonify({"error": "No resumes or job description provided."}), 400

    job_desc_text = request.form['job_desc']
    uploaded_resumes = request.files.getlist('resumes[]')
    
    job_skills_text = extract_skills_from_text(job_desc_text)
    if not job_skills_text:
        return jsonify({"error": "Failed to extract skills from job description."}), 500
    job_skills_set = {s.strip().lower() for s in job_skills_text.split(',') if s.strip()}
    
    candidates = []
    
    for resume_file in uploaded_resumes:
        pdf_data = io.BytesIO(resume_file.read())
        pdf_text = extract_text_from_pdf(pdf_data)
        
        if not pdf_text:
            continue
            
        extracted_info = extract_name_skills_and_contact(pdf_text)
        
        if extracted_info:
            resume_skills_text = extracted_info.get('skills', '')
            resume_skills_set = {s.strip().lower() for s in resume_skills_text.split(',') if s.strip()}
            
            match_percentage = calculate_match_score(resume_skills_text, job_skills_text)
            missing_skills = list(job_skills_set - resume_skills_set)
            
            # Generate a unique pie chart for each candidate
            pie_chart_base64 = generate_pie_chart_base64(match_percentage)

            candidates.append({
                "name": extracted_info.get('name', 'Unknown Candidate'),
                "email": extracted_info.get('email', 'N/A'),
                "phone": extracted_info.get('phone', 'N/A'),
                "match_percentage": match_percentage,
                "missing_skills": missing_skills,
                "pdf_name": resume_file.filename,
                "pie_chart": pie_chart_base64  # Add the pie chart data to the candidate object
            })
    
    candidates.sort(key=lambda x: x['match_percentage'], reverse=True)

    # Generate bar chart
    names = [c["name"] or c["pdf_name"].split('.')[0] for c in candidates]
    scores = [c["match_percentage"] for c in candidates]
    bar_chart_base64 = generate_bar_chart_base64(names, scores)

    return jsonify({"candidates": candidates, "bar_chart": bar_chart_base64})

if __name__ == '__main__':
    app.run(debug=True)