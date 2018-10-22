import pytz

from datetime import datetime
from django.contrib.auth import get_user_model
from django.forms.models import model_to_dict
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from rest_framework import status
from rest_framework.test import APITestCase

from toucon.models import Conference, Permission


tz = pytz.timezone('Europe/Brussels')


class ConferenceTests(APITestCase):
    def setUp(self):
        self.conference = Conference.objects.create(
            code='toucon2017',
            name='Toucon',
            full_name='Test Toucon Conference',
            city='Ghent',
            start_date=datetime.strptime('2018-01-01', '%Y-%m-%d').date(),
            end_date=datetime.strptime('2018-01-03', '%Y-%m-%d').date(),
            registration_start_date=datetime.strptime('2017-11-01', '%Y-%m-%d').date(),
            registration_deadline=tz.localize(datetime.strptime('2018-01-03', '%Y-%m-%d')).astimezone(pytz.utc),
        )
        self.user = get_user_model().objects.create_user('toucon', 'help@toucon.net', 'toucon')

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def set_permissions_and_authenticate(self):
        self.conference.acl.create(user=self.user, level=Permission.ADMIN)
        self.client.force_authenticate(user=self.user)

    def test_list_conference(self):
        with self.assertRaises(NoReverseMatch):
            reverse('v1:conference-list')

    def test_retrieve_conference(self):
        self.authenticate()
        response = self.client.get(reverse('v1:conference-detail', kwargs={'code': 'toucon2017'}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_conference_permissions(self):
        self.set_permissions_and_authenticate()
        response = self.client.get(reverse('v1:conference-detail', kwargs={'code': 'toucon2017'}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_conference(self):
        self.set_permissions_and_authenticate()
        data['name'] = 'Toucon Conf'
        response = self.client.patch(reverse('v1:conference-detail', kwargs={'code': 'toucon2017'}), data)
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
