import pickle
import os.path
from collections import defaultdict
from http import HTTPStatus

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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

    @staticmethod
    def _build_log_groups(logs):
        groups = defaultdict(list)

        for log in logs:
            groups[log.metric.name].append(log)

        return groups

    def export(self, logs):

        groups = GoogleSheets._build_log_groups(logs)
        groups_exported = []

        try:
            response = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()

            found_sheets = {sheet['properties']['title']
                            for sheet in response['sheets']}
            missing_sheets = groups.keys() - found_sheets

            if missing_sheets:
                missing_sheet_requests = [
                    {'addSheet': {'properties': {'title': sheet}}}
                    for sheet in missing_sheets
                ]

                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={'requests': missing_sheet_requests}
                ).execute()

            for metric_name in groups.keys():
                values = []

                for log in groups[metric_name]:
                    if type(log.value) is bytes:
                        log_value = log.value.decode('utf-8')
                    else:
                        log_value = log.value

                    values.append([log.timestamp.isoformat(), log_value])

                resource = {
                  'values': values
                }
                self.service.spreadsheets().values().append(
                    spreadsheetId=self.spreadsheet_id,
                    range='{sheet}!A:A'.format(sheet=metric_name),
                    body=resource,
                    valueInputOption='USER_ENTERED'
                ).execute()

                groups_exported.append(metric_name)

        except HttpError as e:
            if int(e.resp['status']) != HTTPStatus.TOO_MANY_REQUESTS:
                raise

            failed_logs = []

            for group in groups.keys():
                if group not in groups_exported:
                    failed_logs.extend(groups[group])

            raise RateLimitError('Being rate limited, cannot continue exporting', failed_logs)


class RateLimitError(Exception):
    def __init__(self, message, failed_logs):
        super().__init__(message)
        self.failed_logs = failed_logs
