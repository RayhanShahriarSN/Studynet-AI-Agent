# 🚀 Quick Start Guide - RAG AI Agent

## For Complete Beginners

This guide will get you up and running in **15 minutes** even if you've never programmed before!

---

## 📋 What You Need

1. **A computer** (Windows, Mac, or Linux)
2. **Internet connection**
3. **Basic computer skills** (opening files, typing commands)

---

## ⚡ Super Quick Setup (5 minutes)

### Step 1: Download Python
1. Go to https://python.org/downloads/
2. Download Python 3.9 or newer
3. **IMPORTANT**: Check "Add Python to PATH" during installation

### Step 2: Open Command Prompt/Terminal
- **Windows**: Press `Win + R`, type `cmd`, press Enter
- **Mac**: Press `Cmd + Space`, type "Terminal", press Enter
- **Linux**: Press `Ctrl + Alt + T`

### Step 3: Navigate to Project
```bash
cd path/to/your/Studynet-AI-Agent/rag_backend
```

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Create Environment File
Create a file called `.env` in the `rag_backend` folder with this content:
```env
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2025-01-01-preview
CHAT_MODEL_DEPLOYMENT=your_chat_model
EMBEDDING_MODEL_DEPLOYMENT=your_embedding_model
TAVILY_API_KEY=your_tavily_key
```

### Step 6: Start the Server
```bash
python manage.py runserver
```

### Step 7: Open in Browser
Go to: http://localhost:8000/api/

**🎉 You're done!** The AI agent should be running!

---

## 🔧 If Something Goes Wrong

### "Python not found"
- Make sure Python is installed and added to PATH
- Try: `python --version` (should show version number)

### "pip not found"
- Try: `python -m pip install -r requirements.txt`

### "Module not found"
- Make sure you're in the right folder: `rag_backend`
- Try: `pip install django djangorestframework`

### "Port already in use"
- Try: `python manage.py runserver 8001`
- Then go to: http://localhost:8001/api/

---

## 📁 Understanding the Files

### Main Files You'll Work With:
- **`.env`** - Your API keys and settings
- **`pdfs/`** - Put your PDF files here
- **`static/css/style.css`** - Change how it looks
- **`static/js/app.js`** - Change how it works
- **`api/templates/index.html`** - Change the webpage

### Files You DON'T Need to Touch:
- `db.sqlite3` - Database (auto-created)
- `vector_store/` - AI memory (auto-created)
- `manage.py` - Django management
- `requirements.txt` - Dependencies list

---

## 🎨 Making It Your Own

### 1. Change the Look
Edit `static/css/style.css`:
```css
/* Change the background color */
body {
    background: linear-gradient(135deg, #your-color1 0%, #your-color2 100%);
}

/* Change the logo text */
.logo h1 {
    color: #your-color;
}
```

### 2. Change the Text
Edit `api/templates/index.html`:
```html
<!-- Change the welcome message -->
<h2>Welcome to YOUR AI Agent</h2>
<p>Ask me anything about YOUR documents!</p>
```

### 3. Add Your PDFs
1. Put PDF files in the `pdfs/` folder
2. Run: `python load_kb.py`
3. Refresh the webpage

---

## 🔌 API Keys Setup

### Getting Azure OpenAI Keys:
1. Go to https://portal.azure.com
2. Create a new "Azure OpenAI" resource
3. Go to "Keys and Endpoint"
4. Copy the key and endpoint
5. Put them in your `.env` file

### Getting Tavily API Key:
1. Go to https://tavily.com
2. Sign up for free
3. Get your API key
4. Put it in your `.env` file

---

## 🚀 Next Steps

Once it's working:

1. **Read the full documentation**: `COMPREHENSIVE_DOCUMENTATION.md`
2. **Customize the frontend**: Edit files in `static/`
3. **Add your documents**: Put PDFs in `pdfs/`
4. **Deploy online**: Follow the deployment guide

---

## ❓ Need Help?

### Common Questions:

**Q: How do I add more PDFs?**
A: Put them in the `pdfs/` folder and run `python load_kb.py`

**Q: How do I change the colors?**
A: Edit `static/css/style.css` and look for color codes like `#667eea`

**Q: How do I make it work without internet?**
A: You need internet for the AI to work, but you can use it offline for testing

**Q: Can I use it on my phone?**
A: Yes! Just go to `http://your-computer-ip:8000/api/` on your phone

**Q: How do I stop the server?**
A: Press `Ctrl + C` in the command prompt

---

## 🎯 What You've Built

You now have a **RAG AI Agent** that can:
- ✅ Answer questions about your documents
- ✅ Search the web for information
- ✅ Remember conversations
- ✅ Upload new documents
- ✅ Work on any device with a browser

**Congratulations!** 🎉 You've successfully set up an AI system that most people think is impossible to build!

---

## 📚 Learn More

- **Django Basics**: https://docs.djangoproject.com/en/stable/intro/tutorial01/
- **HTML/CSS**: https://www.w3schools.com/
- **JavaScript**: https://www.w3schools.com/js/
- **AI/ML**: https://www.coursera.org/learn/machine-learning

**Happy coding!** 🚀
