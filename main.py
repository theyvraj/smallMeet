import os
import json
import datetime
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

class GoogleMeetCreator:
    def __init__(self, credentials_path):
        self.credentials_path = credentials_path
        self.scopes = ['https://www.googleapis.com/auth/calendar']
        self.service = self._authenticate()
    
    def _authenticate(self):
        creds = None
        token_path = 'token.pickle'
        
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.scopes)
                creds = flow.run_local_server(port=0)
            
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        return build('calendar', 'v3', credentials=creds)
    
    def _encode_event_id(self, event_id):
        import base64
        padded_id = event_id + '=' * ((4 - len(event_id) % 4) % 4)
        return base64.b64encode(padded_id.encode()).decode().replace('=', '')
    
    def create_meet_from_json(self, json_data):
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data
        
        attendees = data.get('attendees', [])
        summary = data.get('summary', 'Google Meet')
        description = data.get('description', '')
        timezone_str = data.get('timezone', 'UTC')
        start_date = data.get('start_date')
        end_date = data.get('end_date')        
        timezone = timezone_str
            
        event = self._create_meet(
            summary, 
            description,
            start_date, 
            end_date,
            attendees, 
            timezone
        )
        
        return event
    
    def _create_meet(self, summary, description, start_time, end_time, attendees, timezone):
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': timezone,
            },
            'end': {
                'dateTime': end_time,
                'timeZone': timezone,
            },
            'conferenceData': {
                'createRequest': {
                    'requestId': f"meet-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
                    'conferenceSolutionKey': {
                        'type': 'hangoutsMeet'
                    }
                }
            }
        }
        
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
        
        event = self.service.events().insert(
            calendarId='primary',
            body=event,
            conferenceDataVersion=1
        ).execute()
        
        return {
            'id': event['id'],
            'summary': event['summary'],
            'description': event['description'],
            'start': event['start']['dateTime'],
            'end': event['end']['dateTime'],
            'meetLink': event.get('hangoutLink', 'No direct link available'),
            'calendarLink': f"https://calendar.google.com/calendar/event?eid={self._encode_event_id(event['id'])}"
        }

if __name__ == "__main__":
    creator = GoogleMeetCreator('credentials.json')    
    json_input = {
        "attendees": ["example@google.com"],
        "summary": "Pepsi Man",
        "description": "Testing this script...",
        "timezone": "UTC",
        "start_date": "2025-03-19T11:46:26",
        "end_date": "2025-03-19T13:08:41"
    }
    
    meeting = creator.create_meet_from_json(json_input)
    
    print("Meeting created successfully:")
    print(f"Summary: {meeting['summary']}")
    print(f"Description: {meeting['description']}")
    print(f"Start: {meeting['start']}")
    print(f"End: {meeting['end']}")
    print(f"Meet Link: {meeting['meetLink']}")
    print(f"Calendar Link: {meeting['calendarLink']}")