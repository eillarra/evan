import { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '',
    redirect: { name: 'registrations' },
    strict: true,
    components: {
      default: () => import('./DashboardApp.vue'),
      drawer: () => import('./DashboardMenu.vue'),
    },
    children: [
      {
        path: '/',
        name: 'registrations',
        strict: true,
        component: () => import('./pages/RegistrationsPage.vue'),
      },
      {
        path: 'events/',
        name: 'events',
        strict: true,
        component: () => import('./pages/EventsPage.vue'),
      },
    ],
  },
];

export default routes;
