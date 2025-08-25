import { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '',
    redirect: { name: 'registration' },
    strict: true,
    components: {
      default: () => import('./RegistrationApp.vue'),
      drawer: () => import('./RegistrationMenu.vue'),
    },
    children: [
      {
        path: '/registration/',
        name: 'old_registration',
        redirect: { name: 'registration' },
      },
      {
        path: '/',
        name: 'registration',
        strict: true,
        component: () => import('./pages/RegistrationPage.vue'),
      },
      {
        path: '/profile/',
        name: 'profile',
        strict: true,
        component: () => import('./pages/ProfilePage.vue'),
      },
      {
        path: '/event/',
        name: 'event',
        strict: true,
        component: () => import('./pages/EventPage.vue'),
      },
      {
        path: '/albums/',
        name: 'albums',
        strict: true,
        component: () => import('./pages/AlbumsPage.vue'),
      },
      /*{
        path: 'attendees/',
        name: 'attendees',
        strict: true,
        component: () => import('./pages/AttendeesPage.vue'),
      },*/
    ],
  },
];

export default routes;
