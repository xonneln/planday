"""
Works with:

https://openapi.planday.com/scheduling/v1.0/shifts

"""

import datetime
import logging

import requests

REFRESH_URL = 'https://openapi-login.planday.com/connect/token'
PUNCH_CLOCK_URL = 'https://openapi.planday.com/scheduling/v1.0/shifts'


class PlandayData(object):

    def __init__(self,
                 client_id,
                 refresh_token,
                 refresh_url=REFRESH_URL,
                 punch_clock_url=PUNCH_CLOCK_URL,
                 attempts=10,
                 branches=None):
        self.client_id = client_id
        self.refresh_token = refresh_token
        self.access_token = ''
        self.refresh_url = refresh_url
        self.punch_clock_url = punch_clock_url
        self.attempts = attempts
        self.branches = branches

    def refresh_access_token(self):
        data = {'client_id': self.client_id,
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token}

        response = requests.post(self.refresh_url, data=data)

        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access_token']
        else:
            logging.error('Not able to get access token {0} {1}'.format(response.status_code, response.text))

    def get_headers(self):
        return {'X-ClientId': self.client_id, 'Authorization': 'Bearer {0}'.format(self.access_token)}

    def get_by_dates(self, dates, snapshots=None, retrieve_historical=False, enhance=True):
        shifts = {}

        for branch, branch_id in self.branches.items():
            branch_snapshot = snapshots.get(branch) if isinstance(snapshots, dict) else None
            shifts[branch] = self.get_by_dates_branch(dates,
                                                      branch_id,
                                                      branch_snapshot=branch_snapshot,
                                                      retrieve_historical=retrieve_historical,
                                                      enhance=enhance)

        return shifts

    def get_by_dates_branch(self, dates, branch_id, branch_snapshot=None, retrieve_historical=False, enhance=True):
        if isinstance(branch_snapshot, dict):
            shifts = {date: data for date, data in branch_snapshot.items() if date in dates}
        else:
            shifts = {}

        def _enhance(shift_data):
            for data in shift_data:
                data['startDateTime'] = datetime.datetime.strptime(data['startDateTime'], '%Y-%m-%dT%H:%M')
                data['endDateTime'] = datetime.datetime.strptime(data['endDateTime'], '%Y-%m-%dT%H:%M')
                data['shiftTime'] = data['endDateTime'] - data['startDateTime']

            return shift_data

        for date in dates:
            if not retrieve_historical and shifts:
                if max(shifts) >= date:
                    if enhance:
                        shift_data = shifts[date]
                        shifts[date] = _enhance(shift_data)
                    continue

            if date not in shifts:
                date_str = '{:%Y-%m-%d}'.format(date)
                url = '{url}?departmentId={branch_id}&from={from_date}&to={to_date}'.format(url=self.punch_clock_url,
                                                                                            branch_id=branch_id,
                                                                                            from_date=date_str,
                                                                                            to_date=date_str)

                # Dirty hack
                for attempt in range(self.attempts):
                    response = requests.get(url, headers=self.get_headers())
                    if response.status_code == 200:
                        break
                    else:
                        logging.info('[shifts_by_branch] status_code={0}'.format(response.status_code))
                        self.refresh_access_token()

                shift_data = response.json()['data']

                if enhance:
                    shift_data = _enhance(shift_data)

                shifts[date] = shift_data

        return shifts
