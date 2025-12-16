<template>
  <div>
    <div class="toolbar">
      <div class="left">
        <el-date-picker
          v-model="selectedMonth"
          type="month"
          placeholder="选择月份"
          value-format="YYYY-MM"
          @change="reloadFinance"
        />
        <el-button type="primary" @click="reloadFinance">刷新报表</el-button>
      </div>
    </div>

    <el-row :gutter="16" class="summary-row">
      <el-col :span="6">
        <el-card>
          <div class="summary-label">总营收</div>
          <div class="summary-value">¥ {{ dashboard.total_revenue }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="summary-label">总工资</div>
          <div class="summary-value">¥ {{ dashboard.total_salary }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="summary-label">其他支出</div>
          <div class="summary-value">¥ {{ dashboard.total_expenses }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="summary-label">净利润</div>
          <div class="summary-value">¥ {{ dashboard.net_profit }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <h3>工资条概览（只读）</h3>
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
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import dayjs from "dayjs";
import api from "../api/client";

const selectedMonth = ref(dayjs().format("YYYY-MM"));
const dashboard = ref({
  total_revenue: 0,
  total_commission: 0,
  total_base_salary: 0,
  total_salary: 0,
  total_expenses: 0,
  net_profit: 0
});
const salarySlip = ref({
  month: "",
  items: []
});

const reloadFinance = async () => {
  if (!selectedMonth.value) return;
  try {
    const [dashRes, slipRes] = await Promise.all([
      api.get("/finance/dashboard", {
        params: { month: selectedMonth.value }
      }),
      api.get("/finance/salary_slip", {
        params: { month: selectedMonth.value }
      })
    ]);
    dashboard.value = dashRes.data;
    salarySlip.value = slipRes.data;
  } catch (err) {
    ElMessage.error("获取财务数据失败");
  }
};

onMounted(() => {
  reloadFinance();
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
}

.summary-row {
  margin-bottom: 16px;
}

.summary-label {
  font-size: 14px;
  color: #999;
}

.summary-value {
  font-size: 18px;
  font-weight: 600;
  margin-top: 4px;
}
</style>
