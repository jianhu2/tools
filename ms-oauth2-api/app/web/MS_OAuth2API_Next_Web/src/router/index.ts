import { createRouter, createWebHistory } from 'vue-router'

import LayoutView from '@/views/layout/index.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'index',
      component: LayoutView,
      redirect: '/home',
      children: [
        {
          path: '/home',
          name: 'home',
          component: () => import('@/views/home/index.vue'),
        },
        {
          path: '/email',
          name: 'email',
          component: () => import('@/views/email/index.vue'),
        },
      ],
    },
  ],
})

export default router
