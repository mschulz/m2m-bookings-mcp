import logging
import json
import base64
from email.mime.text import MIMEText
from google.oauth2 import service_account
from googleapiclient.discovery import build


class GmailOAuth2Handler(logging.Handler):
    def __init__(self, app, recipient, subject, level=logging.ERROR):
        super().__init__(level)

        # Load service account from env
        raw_creds = app.config["GMAIL_SERVICE_ACCOUNT_CREDENTIALS"]
        if not raw_creds:
            raise ValueError(
                "GOOGLE_SERVICE_ACCOUNT_JSON not found in environment variables."
            )
        self.credentials_info = json.loads(raw_creds)

        self.impersonate_user = app.config["FROM_ADDRESS"]
        if not self.impersonate_user:
            raise ValueError("FROM_ADDRESS not found in environment variables.")

        self.recipient = recipient
        self.subject = subject
        self.gmail_service = self._get_gmail_service()

    def _get_gmail_service(self):
        creds = service_account.Credentials.from_service_account_info(
            self.credentials_info,
            scopes=["https://www.googleapis.com/auth/gmail.send"],
            subject=self.impersonate_user,
        )
        return build("gmail", "v1", credentials=creds)

    def emit(self, record):
        try:
            log_entry = self.format(record)

            # Build MIME email
            message = MIMEText(log_entry)
            message["to"] = self.recipient
            message["from"] = self.impersonate_user
            message["subject"] = self.subject

            raw_message = {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}
            self.gmail_service.users().messages().send(
                userId="me", body=raw_message
            ).execute()

        except Exception:
            self.handleError(record)
