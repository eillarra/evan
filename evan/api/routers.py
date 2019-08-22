from rest_framework.routers import DefaultRouter

from evan.api import views


class Router(DefaultRouter):
    def __init__(self, version='v1'):
        super().__init__()

        self.schema_title = 'Evan API {0}'.format(version)

        self.register(r'metadata', views.MetadataViewSet, basename='metadata')
        self.register(r'users', views.UserViewSet, base_name='user')

        self.register(r'events', views.EventViewSet, base_name='event')
        self.register(r'events/(?P<code>[\w-]+)/contents', views.ContentsViewSet, base_name='contents')
        self.register(r'events/(?P<code>[\w-]+)/coupons', views.CouponsViewSet, base_name='coupons')
        self.register(r'events/(?P<code>[\w-]+)/papers', views.PapersViewSet, base_name='papers')
        self.register(r'events/(?P<code>[\w-]+)/registrations', views.RegistrationsViewSet, base_name='registrations')
        self.register(r'events/(?P<code>[\w-]+)/rooms', views.RoomsViewSet, base_name='rooms')
        self.register(r'events/(?P<code>[\w-]+)/sessions', views.SessionsViewSet, base_name='sessions')
        self.register(r'events/(?P<code>[\w-]+)/topics', views.TopicsViewSet, base_name='topics')
        self.register(r'events/(?P<code>[\w-]+)/tracks', views.TracksViewSet, base_name='tracks')
        self.register(r'events/(?P<code>[\w-]+)/venues', views.VenuesViewSet, base_name='venues')

        self.register(r'events/(?P<code>[\w-]+)/register', views.RegistrationCreateViewSet, base_name='register')

        self.register(r'coupons', views.CouponViewSet, base_name='coupon')
        self.register(r'papers', views.PaperViewSet, base_name='paper')
        self.register(r'registrations', views.RegistrationViewSet, base_name='registration')
        self.register(r'rooms', views.RoomViewSet, base_name='room')
        self.register(r'sessions', views.SessionViewSet, base_name='session')
        self.register(r'topics', views.TopicViewSet, base_name='topic')
        self.register(r'tracks', views.TrackViewSet, base_name='track')
        self.register(r'venues', views.VenueViewSet, base_name='venue')
