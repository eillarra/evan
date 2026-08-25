import { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '',
    redirect: { name: 'stats' },
    strict: true,
    components: {
      default: () => import('./EventApp.vue'),
      drawer: () => import('./EventMenu.vue'),
    },
    children: [
      {
        path: '/',
        name: 'stats',
        strict: true,
        component: () => import('./pages/stats/StatsPage.vue'),
      },
      {
        path: 'coupons/',
        name: 'coupons',
        strict: true,
        component: () => import('./pages/coupons/CouponsPage.vue'),
      },
      {
        path: 'dates/',
        name: 'dates',
        strict: true,
        component: () => import('./pages/event/ImportantDatesPage.vue'),
      },
      {
        path: 'emails/',
        name: 'emails',
        strict: true,
        component: () => import('./pages/emails/EmailsPage.vue'),
      },
      {
        path: 'emailplans/',
        name: 'emailplans',
        strict: true,
        component: () => import('./pages/emailplans/EmailPlansPage.vue'),
      },
      {
        path: 'event/',
        name: 'event',
        strict: true,
        component: () => import('./pages/event/EventPage.vue'),
      },
      {
        path: 'keynotes/',
        name: 'keynotes',
        strict: true,
        component: () => import('./pages/keynotes/KeynotesPage.vue'),
      },
      {
        path: 'albums/',
        name: 'albums',
        strict: true,
        component: () => import('./pages/albums/AlbumsPage.vue'),
      },
      {
        path: 'papers/',
        name: 'papers',
        strict: true,
        component: () => import('./pages/papers/PapersPage.vue'),
      },
      {
        path: 'registrations/',
        name: 'registrations',
        strict: true,
        component: () => import('./pages/registrations/RegistrationsPage.vue'),
      },
      {
        path: 'sponsors/',
        name: 'sponsors',
        strict: true,
        component: () => import('./pages/sponsors/SponsorsPage.vue'),
      },
      {
        path: 'sessions/',
        name: 'sessions',
        strict: true,
        component: () => import('./pages/sessions/SessionsPage.vue'),
      },
      {
        path: 'taxonomy/',
        name: 'taxonomy',
        strict: true,
        component: () => import('./pages/taxonomy/TaxonomyPage.vue'),
      },
      {
        path: 'venues/',
        name: 'venues',
        strict: true,
        component: () => import('./pages/venues/VenuesPage.vue'),
      },
      {
        path: 'cms/contents/',
        name: 'contents',
        strict: true,
        component: () => import('./pages/cms/ContentsPage.vue'),
      },
    ],
  },
];

export default routes;
