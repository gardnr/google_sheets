import pickle
import os.path

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from gardnr import constants, drivers


class GoogleSheets(drivers.Exporter):

    blacklist = [constants.IMAGE]

    def setup(self):
        creds = None

        # If modifying these scopes, delete the file token.pickle.
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server()
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('sheets', 'v4', credentials=creds)

    def export(self, logs):
        response = service.spreadsheets().get(spreadsheetId=spreadsheetId).execute()

        sheet_names = [sheet['properties']['title']
                       for sheet in response['sheets']]


        for log in logs:

            if log.metric.name not in sheet_names:
                batch_update_request = {
                    'requests': [{
                        'addSheet': {
                            'properties': {
                                'title': log.metric.name
                            }
                        }
                    }]
                }

                service.spreadsheets().batchUpdate(
                    spreadsheetId=self.sheet_id,
                    body=batch_update_request
                ).execute()

                sheet_names.append(log.metric.name)

            values = [[log.timestamp.isoformat(), log.value]]
            resource = {
              'values': values
            }
            service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range='{sheet}!A:A'.format(log.metric.name),
                body=resource,
                valueInputOption='USER_ENTERED'
            ).execute()
