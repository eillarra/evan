import { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '',
    name: 'public_event',
    strict: true,
    components: {
      default: () => import('./PublicEventApp.vue'),
    },
  },
];

export default routes;
