Prerequisites

Python 3.10+ installed

Git installed

Optional: Virtual environment tool (venv)

1.Create a folder
Create a folder in your desired location named "AI_Agent"

2. Open the folder
Open "AI_Agent" folder in VS code

3. Clone the repository

Clone the repository to "AI_Agent" Folder
git clone https://github.com/RayhanShahriarSN/Studynet-AI-Agent.git

4. Create a Virtual Environment
python -m venv venv

5. Activate the Virtual Environment
.\venv\Scripts\activate

6. Go to Project Folder
i) Right click on "Studynet-AI-Agent" and copy path
ii) cd copied_path

7. Upgrade pip
python -m pip install --upgrade pip

8. Install Dependencies
pip install django fastapi "uvicorn[standard]" python-multipart python-dotenv PyPDF2 langchain openai faiss-cpu sentence-transformers langchain-groq langchain-google-genai langchain-community huggingface-hub rank_bm25 scikit-learn python-decouple django-cors-headers djangorestframework djangorestframework-simplejwt markdown langchain-openai langgraph

9. Update the .env file
put your api keys and endpoints here
OPENAI_API_KEY=
GROQ_API_KEY=
GOOGLE_API_KEY=
AZURE_API_KEY = 
AZURE_ENDPOINT = 
AZURE_DEPLOYMENT =

10. Run FastAPI Backend
uvicorn main:app --reload --port 8000

11. Run Django Frontend (In another terminal)
i) activate vm
.\venv\Scripts\activate

ii) Go to project path (same as 6)

iii) run this code
python manage.py runserver 127.0.0.1:8001

