<template>
  <div class="print-list">
    <el-card>
      <template #header>
        <span>打印管理</span>
      </template>
      
      <el-tabs v-model="activeTab">
        <el-tab-pane label="延生法会打印" name="yansheng">
          <PrintTable :type="0" />
        </el-tab-pane>
        <el-tab-pane label="往生法会打印" name="wangsheng">
          <PrintTable :type="1" />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import PrintTable from './PrintTable.vue'

const activeTab = ref('yansheng')
</script>

<style scoped>
.print-list {
  height: 100%;
}
</style>
