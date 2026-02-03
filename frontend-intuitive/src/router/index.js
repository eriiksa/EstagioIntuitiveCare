import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import OperadoraDetails from '../views/OperadoraDetails.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/operadora/:cnpj', name: 'details', component: OperadoraDetails, props: true }
  ]
})

export default router