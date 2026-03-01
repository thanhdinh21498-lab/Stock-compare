# PyCharm Mini ChatGPT API Agent (Terminal + File Workflow)

This is a small, practical "mini Copilot" you can run inside PyCharm without opening a browser.
It uses the OpenAI API via the official Python SDK.

## 1) Create a virtual environment
In PyCharm:
- File → Settings → Project → Python Interpreter → Add Interpreter → Virtualenv

## 2) Install dependencies
Open PyCharm Terminal in this project folder:
```bash
pip install -r requirements.txt
```

## 3) Set your API key
### Option A (recommended): environment variable
Windows PowerShell:
```powershell
setx OPENAI_API_KEY "YOUR_KEY_HERE"
```
macOS/Linux:
```bash
export OPENAI_API_KEY="YOUR_KEY_HERE"
```

### Option B: .env file (convenient for local dev)
1) Copy `.env.example` to `.env`
2) Put your key in `.env`

## 4) Run (interactive)
```bash
python -m a.main
```

Interactive commands:
- `/code`      -> code-only responses (default)
- `/explain`   -> short explanation + code
- `/model X`   -> switch model name
- `/add path`  -> add a local file as context
- `/files`     -> list currently loaded context files
- `/clearfiles`
- `/quit`

## 5) Run (file-based)
Write your prompt into `question.txt` (in project root), then:
```bash
python -m a.main --question-file question.txt --out answer.py
```

## 6) Run (one-shot question)
```bash
python -m a.main --question "Write a pandas function to..." --out answer.py
```

## Notes
- This project does NOT open any browser UI.
- It requires internet access for API calls.
- You control output: print to terminal and/or write to a file.
