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
        path: '/',
        name: 'registration',
        strict: true,
        component: () => import('./pages/RegistrationPage.vue'),
      },
      {
        path: 'attendees/',
        name: 'attendees',
        strict: true,
        component: () => import('./pages/AttendeesPage.vue'),
      },
    ],
  },
];

export default routes;
