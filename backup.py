import os
import json
import datetime
import pytz
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

class GoogleMeetCreator:
    def __init__(self, credentials_path):
        """Initialize the Meet creator with credentials path."""
        self.credentials_path = credentials_path
        self.scopes = ['https://www.googleapis.com/auth/calendar']
        self.service = self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar API."""
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
    
    def create_meet_from_json(self, json_data):
        """Create a single Google Meet event from JSON input."""
        if isinstance(json_data, str):
            # Parse JSON string if provided
            data = json.loads(json_data)
        else:
            # Assume already parsed JSON object
            data = json_data
        
        # Extract data from JSON
        attendees = data.get('attendees', [])
        summary = data.get('summary', 'Google Meet')
        description = data.get('description', '')
        timezone_str = data.get('timezone', 'UTC')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # Convert timezone string to pytz timezone
        if timezone_str == 'IST':
            timezone = 'Asia/Kolkata'
        else:
            timezone = timezone_str
            
        # Create a single meeting with the exact start and end times
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
        """Create a single Google Meet event."""
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
            'meetLink': event.get('hangoutLink', 'No direct link available')
        }


# Example usage
if __name__ == "__main__":
    # Initialize the creator
    creator = GoogleMeetCreator('credentials.json')
    
    # Example JSON input
    json_input = {
        "attendees": ["attendee1@example.com", "attendee2@example.com"],
        "summary": "Test Meeting",
        "description": "there will be meeting on 19-03-2025.",
        "timezone": "IST",
        "start_date": "2025-03-19T09:00:00",
        "end_date": "2025-03-19T17:00:00"
    }
    
    # Create a single meeting
    meeting = creator.create_meet_from_json(json_input)
    
    # Print meeting details
    print("Meeting created successfully:")
    print(f"Summary: {meeting['summary']}")
    print(f"Description: {meeting['description']}")
    print(f"Start: {meeting['start']}")
    print(f"End: {meeting['end']}")
    print(f"Meet Link: {meeting['meetLink']}")