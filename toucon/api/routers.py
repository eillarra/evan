from rest_framework.routers import DefaultRouter

from toucon.api import views


class Router(DefaultRouter):
    def __init__(self, version='v1'):
        super().__init__()

        self.schema_title = 'Toucon API {0}'.format(version)

        if version == 'v1':
            self.register(r'conferences', views.ConferenceViewSet, base_name='conference')
            self.register(r'conferences/(?P<code>[\w-]+)/coupons', views.CouponsViewSet, base_name='coupons')
            self.register(r'conferences/(?P<code>[\w-]+)/papers', views.PapersViewSet, base_name='papers')
            self.register(r'conferences/(?P<code>[\w-]+)/registrations', views.RegistrationsViewSet,
                          base_name='registrations')
            self.register(r'conferences/(?P<code>[\w-]+)/rooms', views.RoomsViewSet, base_name='rooms')
            self.register(r'conferences/(?P<code>[\w-]+)/sessions', views.SessionsViewSet, base_name='sessions')
            self.register(r'conferences/(?P<code>[\w-]+)/topics', views.TopicsViewSet, base_name='topics')
            self.register(r'conferences/(?P<code>[\w-]+)/tracks', views.TracksViewSet, base_name='tracks')
            self.register(r'conferences/(?P<code>[\w-]+)/venues', views.VenuesViewSet, base_name='venues')

            self.register(r'coupons', views.CouponViewSet, base_name='coupon')
            self.register(r'papers', views.PaperViewSet, base_name='paper')
            self.register(r'registrations', views.RegistrationViewSet, base_name='registration')
            self.register(r'rooms', views.RoomViewSet, base_name='room')
            self.register(r'sessions', views.SessionViewSet, base_name='session')
            self.register(r'topics', views.TopicViewSet, base_name='topic')
            self.register(r'tracks', views.TrackViewSet, base_name='track')
            self.register(r'venues', views.VenueViewSet, base_name='venue')

            self.register(r'users', views.UserViewSet, base_name='user')
