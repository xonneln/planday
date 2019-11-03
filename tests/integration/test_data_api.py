from unittest import TestCase
import integration.data_api
import mock
import requests
import tests.integration.test_data
import datetime


class TestPlandayData(TestCase):

    def setUp(self):
        self.client_id = '123a-11cb-11bb-bae7'
        self.refresh_token = 'RjY2XjM5XzA2OWJjuE9c'
        self.branches = {'Miami Beach': '123'}

        self.planday = integration.data_api.PlandayData(self.client_id, self.refresh_token, branches=self.branches)

        self.json = tests.integration.test_data.SHIFT_DATA

    @mock.patch('integration.data_api.requests', autospec=True)
    def test_get_by_dates(self, mock_requests):
        mock_response = mock.Mock(spec=requests.models.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': self.json}

        mock_requests.get.return_value = mock_response

        dates = [datetime.date(2019, 11, 1)]

        shifts = self.planday.get_by_dates(dates, enhance=False)

        for branch in shifts.keys():
            for date in dates:
                self.assertEqual(shifts[branch][date], self.json)
