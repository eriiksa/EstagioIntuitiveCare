<template>
  <div class="container">
    <h1>Dashboard Operadoras</h1>
    
    <div v-if="loadingStats">Carregando estatísticas...</div>
    <div v-else class="stats-panel">
      <div class="chart-container">
        <h3>Distribuição de Despesas por UF</h3>
        <canvas id="ufChart"></canvas>
      </div>
      <div class="cards">
        <div class="card">
          <h3>Consistência</h3>
          <p>{{ stats?.consistencia?.qtd_operadoras_consistentes || 0 }}</p>
          <small>Operadoras acima da média em >2 trimestres</small>
        </div>
      </div>
    </div>

    <hr>

    <div class="search-bar">
      <input 
        v-model="searchQuery" 
        @input="debouncedSearch" 
        placeholder="Buscar por Razão Social ou CNPJ..." 
        type="text"
      />
    </div>

    <div v-if="loadingTable" class="loading">Carregando operadoras...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    
    <table v-else>
      <thead>
        <tr>
          <th>CNPJ</th>
          <th>Razão Social</th>
          <th>UF</th>
          <th>Ações</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="op in operadoras" :key="op.registro_ans">
          <td>{{ op.cnpj }}</td>
          <td>{{ op.razao_social }}</td>
          <td>{{ op.uf }}</td>
          <td>
            <router-link :to="{ name: 'details', params: { cnpj: op.cnpj }}">
              Ver Detalhes
            </router-link>
          </td>
        </tr>
      </tbody>
    </table>

    <div class="pagination">
      <button :disabled="page === 1" @click="changePage(page - 1)">Anterior</button>
      <span>Página {{ page }}</span>
      <button :disabled="operadoras.length < limit" @click="changePage(page + 1)">Próxima</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'
import Chart from 'chart.js/auto'

const api = axios.create({ baseURL: 'http://127.0.0.1:5000/api' })

// Estado
const operadoras = ref([])
const stats = ref(null)
const page = ref(1)
const limit = ref(10)
const searchQuery = ref('')
const loadingTable = ref(false)
const loadingStats = ref(false)
const error = ref(null)
let chartInstance = null

// Buscar Estatísticas (Gráfico)
const fetchStats = async () => {
  loadingStats.value = true
  try {
    const res = await api.get('/estatisticas')
    stats.value = res.data
    renderChart(res.data.distribuicao_uf)
  } catch (e) {
    console.error("Erro stats:", e)
  } finally {
    loadingStats.value = false
  }
}

// Renderizar Gráfico
const renderChart = (dataUf) => {
  const ctx = document.getElementById('ufChart')
  if (chartInstance) chartInstance.destroy()
  
  chartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: dataUf.map(item => item.uf),
      datasets: [{
        label: 'Despesa Total (R$)',
        data: dataUf.map(item => item.despesa_total),
        backgroundColor: '#36A2EB'
      }]
    }
  })
}

// Buscar Operadoras (Tabela)
const fetchOperadoras = async () => {
  loadingTable.value = true
  error.value = null
  try {
    const params = { page: page.value, limit: limit.value }
    if (searchQuery.value) params.search = searchQuery.value
    
    const res = await api.get('/operadoras', { params })
    operadoras.value = res.data.data // Ajuste conforme seu retorno em api.py
  } catch (e) {
    error.value = "Erro ao carregar dados. Verifique a API."
  } finally {
    loadingTable.value = false
  }
}

// Debounce simples para a busca (espera usuário parar de digitar)
let timeout = null
const debouncedSearch = () => {
  clearTimeout(timeout)
  timeout = setTimeout(() => {
    page.value = 1
    fetchOperadoras()
  }, 500)
}

const changePage = (newPage) => {
  page.value = newPage
  fetchOperadoras()
}

onMounted(() => {
  fetchOperadoras()
  fetchStats()
})
</script>

<style scoped>
/* Estilos básicos para visualização rápida */
.container { max-width: 900px; margin: 0 auto; padding: 20px; font-family: sans-serif; }
.stats-panel { display: flex; gap: 20px; margin-bottom: 30px; }
.chart-container { flex: 2; height: 300px; }
.cards { flex: 1; display: flex; flex-direction: column; gap: 10px; }
.card { padding: 15px; background: #f4f4f4; border-radius: 8px; text-align: center; }
table { width: 100%; border-collapse: collapse; margin-top: 20px; }
th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
.pagination { margin-top: 15px; display: flex; gap: 10px; justify-content: center; }
button { padding: 8px 16px; cursor: pointer; }
.loading { color: #666; font-style: italic; margin: 20px 0; }
.error { color: red; margin: 20px 0; }
</style>