<template>
  <header>
    <div class="wrapper">
      <nav>
        </nav>
    </div>
  </header>

  <RouterView />
</template>

<script setup>
import { RouterView } from 'vue-router'
</script>

<style>
/* Reset básico para não quebrar o layout */
body { margin: 0; font-family: Arial, sans-serif; }
</style>