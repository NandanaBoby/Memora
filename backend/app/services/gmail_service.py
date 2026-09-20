import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying scopes, delete token.json and re-authenticate
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # app/
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_PATH = os.path.join(BASE_DIR, 'token.json')


def get_gmail_service():
    """Authenticates and returns a Gmail API service object."""
    creds = None

    # token.json stores the user's access/refresh tokens after first auth
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # If no valid credentials, log in via browser
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for next time
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    return service


def fetch_recent_emails(max_results=10):
    """Fetches a batch of recent emails: id, subject, sender, date, snippet, body text."""
    service = get_gmail_service()
    results = service.users().messages().list(
        userId='me', maxResults=max_results, labelIds=['INBOX']
    ).execute()
    messages = results.get('messages', [])

    emails = []
    for msg_meta in messages:
        msg = service.users().messages().get(
            userId='me', id=msg_meta['id'], format='full'
        ).execute()

        headers = msg['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(no subject)')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), '(unknown sender)')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), '')

        body = extract_body(msg['payload'])

        emails.append({
            'gmail_id': msg['id'],
            'subject': subject,
            'sender': sender,
            'date': date,
            'snippet': msg.get('snippet', ''),
            'body': body,
        })

    return emails


def extract_body(payload):
    """Extracts plain text body from a Gmail message payload, handling nested parts."""
    if 'parts' in payload:
        for part in payload['parts']:
            if part.get('mimeType') == 'text/plain':
                data = part['body'].get('data')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            elif 'parts' in part:
                result = extract_body(part)
                if result:
                    return result
    else:
        data = payload.get('body', {}).get('data')
        if data:
            return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    return ''


if __name__ == '__main__':
    from app.database import SessionLocal
    from app.models.email import Email

    emails = fetch_recent_emails(max_results=10)
    db = SessionLocal()

    saved_count = 0
    for e in emails:
        existing = db.query(Email).filter(Email.gmail_id == e['gmail_id']).first()
        if existing:
            continue  # skip duplicates

        db_email = Email(
            gmail_id=e['gmail_id'],
            subject=e['subject'],
            sender=e['sender'],
            date=e['date'],
            snippet=e['snippet'],
            body=e['body'],
        )
        db.add(db_email)
        saved_count += 1

    db.commit()
    db.close()
    print(f"Saved {saved_count} new emails to the database.")