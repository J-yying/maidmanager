<template>
  <div>
    <div class="toolbar">
      <div class="left">
        <h3>薪资管理</h3>
        <el-date-picker
          v-model="selectedMonth"
          type="month"
          placeholder="选择月份"
          value-format="YYYY-MM"
          @change="reload"
        />
        <el-button type="primary" @click="reload">刷新</el-button>
      </div>
    </div>

    <el-card>
      <h3>工资条</h3>
      <el-table :data="salarySlip.items" border style="width: 100%">
        <el-table-column prop="staff_id" label="员工ID" width="80" />
        <el-table-column prop="staff_name" label="姓名" />
        <el-table-column prop="base_salary" label="底薪" />
        <el-table-column prop="commission_total" label="提成总额" />
        <el-table-column prop="total_salary" label="应发工资" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import dayjs from "dayjs";
import api from "../api/client";

const selectedMonth = ref(dayjs().format("YYYY-MM"));
const salarySlip = ref({
  month: "",
  items: []
});

const reload = async () => {
  if (!selectedMonth.value) return;
  try {
    const { data } = await api.get("/finance/salary_slip", {
      params: { month: selectedMonth.value }
    });
    salarySlip.value = data;
  } catch (err) {
    ElMessage.error("获取工资条失败");
  }
};

onMounted(() => {
  reload();
});
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.toolbar .left {
  display: flex;
  gap: 8px;
  align-items: center;
}
</style>

