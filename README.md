# Chat1Min

**60 seconds. One stranger. No names. No history.**

Chat1Min is a minimalist, anonymous, real-time 1-minute chat app.  
When two people are online at the same time, they get instantly paired.  
You have exactly 60 seconds to talk — then the entire conversation vanishes forever.

Live demo (if deployed): https://chat1min.pythonanywhere.com/

## Features

- Completely anonymous — no usernames shown to the other person (only internally for pairing)
- 60-second countdown with color-changing progress bar
- Messages disappear forever when time runs out or someone leaves
- Beautiful dark purple aesthetic with particle background
- No registration, no cookies (except a temporary session ID), no logs kept
- Pure chaos, real moments

## Tech Stack

- Python + Flask (backend)
- Pure HTML/CSS/JS (frontend – no framework)
- LeCatchu (lightweight custom encryption for user DB)
- Thread-safe in-memory matching + encrypted on-disk persistence

## Quick Start (Local Development)

```bash
# 1. Clone the repo
git clone https://github.com/aertsimon90/chat1min.git
cd chat1min

# 2. (Recommended) Create a virtual environment
python -m venv venv
source venv/bin/activate    # Linux/Mac
# or
venv\Scripts\activate       # Windows

# 3. Install dependencies
pip install flask

# 4. Run the app
python app.py
```

Open http://127.0.0.1:5000 in two different browser windows/tabs and watch the magic.

## Project Structure

```
├── app.py                  # Main Flask application
├── users_db.json.lc        # Encrypted user database (auto-created)
├── lckey.txt               # Encrypted master key (auto-created)
├── index.html              # Landing page
├── get_account.html        # Sign-up / login page (minimal)
├── loading.html            # Matching screen
├── chat.html               # Active chat interface
├── LeCatchu.py             # LeCatchu module
├── favicon.ico
└── logo.png
```

## Security Notes

- Passwords are iteratively SHA-256 hashed (≥16 + random extra rounds)
- Session IDs are high-entropy hashes
- All stored data is encrypted with a unique per-installation key
- No personal data is ever stored or logged

## Deployment

The app is ready for any WSGI server (Gunicorn, uWSGI, Waitress) or platforms like Render, Railway, Fly.io, etc.

Example with Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Contributing

Feel free to open issues or PRs!  
Ideas: sound notifications, typing indicators, mobile PWA install, dark mode toggle (it's already dark).

## License

MIT © 2025 Simon Scap – Free to use, modify, and deploy.
