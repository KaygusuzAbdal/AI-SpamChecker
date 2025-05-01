from __future__ import print_function
import base64
import os.path
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# required to access Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

class GmailConnector:
    def __init__(self, credentials_path='mail_connector/credentials/gmail.json', token_path='mail_connector/credentials/gmail_token.pkl'):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = self.authenticate()

    def authenticate(self):
        creds = None

        # use previously saved token if available
        if os.path.exists(self.token_path):
            # 'rb' -> read-binary because token is stored in binary format
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)

        # if no valid token exists, request a new one
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # start Google OAuth process to access Gmail
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                # runs a local web server to complete Gmail authorization
                creds = flow.run_local_server(port=0)

            # save the token ('wb' -> write-binary)
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)

        # build the Gmail service
        service = build('gmail', 'v1', credentials=creds)
        return service

    def get_messages(self, unread=True, exclude_labels=None, max_results=10):
        # fetch messages from inbox (unread or all)
        query= 'is:unread ' if unread else ''  # filter based on user preference

        # exclude mails with these labels
        if exclude_labels:
            for lbl in exclude_labels:
                query += f'-label:{lbl} '
        
        try:
            results = self.service.users().messages().list(
                userId='me', labelIds=['INBOX'], q=query, maxResults=max_results
            ).execute()
            messages = results.get('messages', [])
        except Exception as e:
            print(f"[!] An error occurred while fetching messages: {e}")
            messages = []

        return messages
    
    # fetch unread or all inbox messages
    def get_unread_messages(self, unread=True, max_results=10):
        query = 'is:unread' if unread else ''  # filter based on user preference

        try:
            results = self.service.users().messages().list(
                userId='me', labelIds=['INBOX'], q=query, maxResults=max_results
            ).execute()
            messages = results.get('messages', [])
        except Exception as e:
            print(f"[!] An error occurred while fetching messages: {e}")
            messages = []

        return messages

    # get the content of a specific message
    def get_message_detail(self, message_id):
        try:
            # fetch full details of the message using its message_id
            message = self.service.users().messages().get(userId='me', id=message_id, format='full').execute()
            headers = message['payload'].get('headers', [])

            subject = ''
            sender = ''
            auth_results = ''

            # extract header values (subject, from, auth-results)
            for header in headers:
                if header['name'].lower() == 'subject':
                    subject = header['value']
                elif header['name'].lower() == 'from':
                    sender = header['value']
                elif header['name'].lower() == 'authentication-results':
                    auth_results = header['value']

            body = ''
            # emails can have multiple parts (HTML + TEXT)
            parts = message['payload'].get('parts', [])
            # if parts exist, extract only the text/plain part
            if parts:
                for part in parts:
                    if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                        data = part['body']['data']
                        body = base64.urlsafe_b64decode(data).decode("utf-8")
                        break
            else:
                # if no parts, get the body directly
                body_data = message['payload']['body'].get('data')
                if body_data:
                    body = base64.urlsafe_b64decode(body_data).decode("utf-8")

            return {
                'id': message_id,
                'from': sender,
                'subject': subject,
                'body': body,
                'auth_results': auth_results
            }

        except Exception as e:
            print(f"[!] Could not fetch message details (ID: {message_id}): {e}")
            return {
                'id': message_id,
                'from': '',
                'subject': '',
                'body': '',
                'auth_results': ''
            }
    
    # check if a message has a specific label
    def check_message_labels(self, message_id, labels_to_check):
        # fetch message details
        msg = self.service.users().messages().get(userId='me', id=message_id).execute()
        label_ids = msg.get('labelIds', [])

        # convert to list if a single string is provided
        if isinstance(labels_to_check, str):
            labels_to_check = [labels_to_check]

        # fetch all labels
        all_labels = self.service.users().labels().list(userId='me').execute().get('labels', [])
        # map label names to their IDs
        label_name_to_id = {lbl['name'].lower(): lbl['id'] for lbl in all_labels}

        result = {}

        for label in labels_to_check:
            label_lower = label.lower()
            label_id = label_name_to_id.get(label_lower)

            # label not found
            if not label_id:
                # print(f"[!] Label '{label}' not found in Gmail.")
                result[label] = False
                continue

        is_present = label_id in label_ids
        result[label] = is_present

        return result

    # add a label to a message
    def add_message_label(self, message_id, label_name, bg_color=None, text_color="#ffffff"):
        
        # first, check if the message already has the label
        check_result = self.check_message_labels(message_id, label_name)
        # label already exists, exit function
        if check_result.get(label_name, False):
            print(f"[!] Mail with ID {message_id} already has the label '{label_name.upper()}'. Skipping..\n")
            return  # label already exists, exit function

        # find label id
        labels = self.service.users().labels().list(userId='me').execute()
        label_id = None
        for lbl in labels['labels']:
            if lbl['name'].lower() == label_name.lower():
                label_id = lbl['id']
                break

        # if label doesn't exist, create a new one
        if not label_id:
            # set colors
            if label_name.lower() == 'spam' and bg_color==None:
                bg_color = '#cc3a21'  # red
            elif label_name.lower() == 'safe' and bg_color==None:
                bg_color = '#16a766'  # green
            else:
                bg_color = '#9AA0A6' # default gray
            
            label = {
                'name': label_name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show',
                'color': {
                    'backgroundColor': bg_color,
                    'textColor': text_color
                }
            }
            created_label = self.service.users().labels().create(userId='me', body=label).execute()
            label_id = created_label['id']
            print(f"[+] New label created: {label_name.upper()} (ID: {label_id})")

        # add label to the message
        self.service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'addLabelIds': [label_id]}
        ).execute()
        print(f"[+] Label '{label_name}' added to mail with ID {message_id}.\n")

# example usage
# connector = GmailConnector()
# messages = connector.get_messages()
# for msg in messages:
#     print(connector.get_message_detail(msg['id']))
