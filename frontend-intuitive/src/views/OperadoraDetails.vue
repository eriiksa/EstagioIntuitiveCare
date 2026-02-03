<template>
  <div class="container">
    <router-link to="/">← Voltar</router-link>
    
    <div v-if="loading" class="loading">Carregando detalhes...</div>
    <div v-else-if="operadora">
      <h1>{{ operadora.razao_social }}</h1>
      <div class="info">
        <p><strong>CNPJ:</strong> {{ operadora.cnpj }}</p>
        <p><strong>Registro ANS:</strong> {{ operadora.registro_ans }}</p>
        <p><strong>UF:</strong> {{ operadora.uf }}</p>
        <p><strong>Modalidade:</strong> {{ operadora.modalidade }}</p>
      </div>

      <h2>Histórico de Despesas</h2>
      <table v-if="despesas.length">
        <thead>
          <tr>
            <th>Ano</th>
            <th>Trimestre</th>
            <th>Conta</th>
            <th>Valor (R$)</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(d, index) in despesas" :key="index">
            <td>{{ d.ano }}</td>
            <td>{{ d.trimestre }}º</td>
            <td>{{ d.conta }}</td>
            <td>{{ formatCurrency(d.valor) }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else>Nenhum histórico de despesas encontrado.</p>
    </div>
    <div v-else class="error">Operadora não encontrada.</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const cnpj = route.params.cnpj
const api = axios.create({ baseURL: 'http://127.0.0.1:5000/api' })

const operadora = ref(null)
const despesas = ref([])
const loading = ref(true)

const formatCurrency = (value) => {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
}

onMounted(async () => {
  try {
    // Busca dados cadastrais
    const resOp = await api.get(`/operadoras/${cnpj}`)
    operadora.value = resOp.data

    // Busca histórico de despesas
    const resDesp = await api.get(`/operadoras/${cnpj}/despesas`)
    despesas.value = resDesp.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.container { max-width: 800px; margin: 0 auto; padding: 20px; font-family: sans-serif; }
.info { background: #f9f9f9; padding: 15px; border-radius: 8px; margin: 20px 0; }
table { width: 100%; border-collapse: collapse; }
th, td { border-bottom: 1px solid #ddd; padding: 10px; text-align: left; }
</style>