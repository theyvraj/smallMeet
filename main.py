import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

class GoogleMeetCreator:
    def __init__(self, credentials_path):
        import os.path
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        # If modifying these scopes, delete the file token.json.
        SCOPES = ['https://www.googleapis.com/auth/calendar']

        creds = None
        # The file token.json stores the user's access and refresh tokens
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_info(json.load(open('token.json')))

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        self.service = build('calendar', 'v3', credentials=creds)

    def _encode_event_id(self, event_id):
        import base64
        return base64.b64encode(f"{event_id}".encode()).decode().rstrip('=')

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

    def create_meet_from_json(self, json_data):
        summary = json_data.get('summary', 'New Meeting')
        description = json_data.get('description', '')
        start_date = json_data.get('start_date')
        end_date = json_data.get('end_date')
        attendees = json_data.get('attendees', [])
        timezone = json_data.get('timezone', 'UTC')

        return self._create_meet(summary, description, start_date, end_date, attendees, timezone)

# Create a global instance of GoogleMeetCreator
import json
creator = GoogleMeetCreator('credentials.json')

@app.route('/create-meet', methods=['POST'])
def create_meet():
    try:
        json_input = request.json
        meeting = creator.create_meet_from_json(json_input)

        # Format the response according to the specified structure
        response = {
            "Summary": meeting['summary'],
            "Description": meeting['description'],
            "Start": meeting['start'],
            "End": meeting['end'],
            "Meet Link": meeting['meetLink'],
            "Calendar Link": meeting['calendarLink']
        }

        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Run the Flask app on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)