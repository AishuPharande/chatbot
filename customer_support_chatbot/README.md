# Customer Support Chatbot (Python + Flask + MySQL)

A beginner-friendly portfolio project with an NLP intent-classification FAQ chatbot, customer registration/login, MySQL-backed support tickets, ticket tracking, and an admin dashboard.

## Features
- NLP intent-classification chatbot FAQ responses
- AJAX chat (no page refresh)
- Password hashing and session-based login
- MySQL user and ticket tables
- Ticket creation for escalated/unknown issues when signed in
- Customer ticket history
- Admin ticket status updates and replies
- Responsive HTML/CSS interface

## Requirements
- Python 3.10+
- MySQL Server (or XAMPP MySQL)
- A terminal and code editor

## Setup on Windows

1. Extract this folder and open it in VS Code.
2. Open a terminal in this folder and create a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use `\.venv\Scripts\python.exe` directly or activate from Command Prompt with `.venv\Scripts\activate.bat`.

3. Install packages:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Create the database and tables. In MySQL Workbench, open `schema.sql` and execute it, or run:

   ```powershell
   mysql -u root -p < schema.sql
   ```

   If your MySQL runs on port 3307, use `mysql -u root -p -P 3307 < schema.sql`.

5. Copy `.env.example` to `.env` and set your MySQL host, port, username, password, database, and a long random `SECRET_KEY`. Do not commit `.env` to source control.

6. Start the application:

   ```powershell
   python app.py
   ```

7. Open `http://127.0.0.1:5001`.

## Create an admin account

1. Register a normal account through the website.
2. In MySQL Workbench, run the following with the email you registered:

   ```sql
   USE customer_support;
   UPDATE users SET role = 'admin' WHERE email = 'your-email@example.com';
   ```
3. Sign out and sign back in. The Admin link will appear.

Do not expose an admin-role change route to the public. Promote admins manually or through a separately protected administrative process.

## Customize the FAQ bot

Edit `FAQS` in `chatbot.py`. Each entry has a tuple of keywords, a reply, and a Boolean indicating whether the issue should create a ticket. This is keyword matching, not an AI/LLM model; it is intentionally simple for learning.

## Troubleshooting
- `ModuleNotFoundError`: activate the virtual environment and run `python -m pip install -r requirements.txt`.
- MySQL connection error: check that MySQL is running and `.env` has the correct port and credentials.
- `Unknown database`: execute `schema.sql` first.
- Chat says a ticket was not created: sign in first; anonymous users can chat but ticket persistence is only available to signed-in users.

## Production hardening before deployment
Set a strong secret key, disable debug mode, use HTTPS, add rate limiting and login throttling, configure secure session cookies, validate email addresses, add password reset and email delivery, and use a managed secret store. Add authorization checks and audit logging before using real customer data. Never ask customers to provide passwords, OTPs, or full card details.


## NLP intent detection

The chatbot now classifies messages into intents such as greeting, support hours, password help, refunds, billing, order status, human-agent requests, thanks, and goodbye. It uses `TfidfVectorizer` with unigrams/bigrams and `LogisticRegression`. Messages below the confidence threshold use a safe fallback and can be escalated to a ticket.

To test the intent classifier:

```powershell
python -m unittest -v
```

To improve classification, add multiple natural phrasings for each intent in `INTENT_EXAMPLES` in `chatbot.py`. Keep examples free of real customer personal information. The current training examples are a starter dataset, not a production-grade language model. Review predictions and tune `CONFIDENCE_THRESHOLD` using a separate validation set before production use.
