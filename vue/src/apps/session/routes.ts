import { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '',
    redirect: { name: 'session' },
    strict: true,
    components: {
      default: () => import('./SessionApp.vue'),
      drawer: () => import('./SessionMenu.vue'),
    },
    children: [
      {
        path: '/',
        name: 'session',
        strict: true,
        component: () => import('./pages/SessionPage.vue'),
      },
      {
        path: 'committees/',
        name: 'committees',
        strict: true,
        component: () => import('./pages/CommitteesPage.vue'),
      },
      {
        path: 'dates/',
        name: 'dates',
        strict: true,
        component: () => import('./pages/ImportantDatesPage.vue'),
      },
    ],
  },
];

export default routes;
