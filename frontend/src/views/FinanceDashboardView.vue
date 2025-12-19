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
        <el-table-column label="套餐统计" min-width="200">
          <template #default="{ row }">
            <div v-if="row.packages && row.packages.length">
              <div
                v-for="p in row.packages"
                :key="`${row.staff_id}-${p.package_id || 'none'}-${p.order_count}`"
                class="pkg-row"
              >
                <span class="pkg-name">{{ p.package_name || "未指定套餐" }}</span>
                <span class="pkg-count">×{{ p.order_count }}</span>
                <span class="pkg-amount">￥{{ formatNumber(p.total_amount) }}</span>
              </div>
            </div>
            <span v-else class="muted">-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12">
        <el-card>
          <h3>员工出勤（按月汇总）</h3>
          <el-table :data="attendance.items" border style="width: 100%">
            <el-table-column prop="staff_name" label="员工" />
            <el-table-column prop="shift_days" label="排班天数" width="100" />
            <el-table-column label="排班时长（小时）">
              <template #default="{ row }">
                {{ formatHours(row.shift_hours) }}
              </template>
            </el-table-column>
            <el-table-column prop="completed_order_count" label="完成订单数" width="120" />
            <el-table-column label="完成时长（小时）">
              <template #default="{ row }">
                {{ formatHours(row.completed_order_hours) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <h3>排班概览（按月）</h3>
          <el-descriptions :column="1" size="small" border>
            <el-descriptions-item label="总排班时长">
              {{ formatHours(rosterOverview.total_shift_hours) }}
            </el-descriptions-item>
            <el-descriptions-item label="套餐总钟数">
              {{ formatHours(rosterOverview.total_package_hours) }}
            </el-descriptions-item>
            <el-descriptions-item label="排班天数">
              {{ rosterOverview.shift_days }}
            </el-descriptions-item>
            <el-descriptions-item label="日均时长">
              {{ formatHours(rosterOverview.avg_daily_shift_hours) }}
            </el-descriptions-item>
            <el-descriptions-item label="最早开始">
              {{ rosterOverview.earliest_start || "-" }}
            </el-descriptions-item>
            <el-descriptions-item label="最晚结束">
              {{ rosterOverview.latest_end || "-" }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
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
const attendance = ref({
  month: "",
  items: []
});
const rosterOverview = ref({
  month: "",
  total_shift_hours: 0,
  shift_days: 0,
  avg_daily_shift_hours: 0,
  earliest_start: "",
  latest_end: ""
});

const reloadFinance = async () => {
  if (!selectedMonth.value) return;
  try {
    const [dashRes, slipRes, attRes, rosterRes] = await Promise.all([
      api.get("/finance/dashboard", {
        params: { month: selectedMonth.value }
      }),
      api.get("/finance/salary_slip", {
        params: { month: selectedMonth.value }
      }),
      api.get("/finance/attendance", {
        params: { month: selectedMonth.value }
      }),
      api.get("/finance/roster_overview", {
        params: { month: selectedMonth.value }
      })
    ]);
    dashboard.value = dashRes.data;
    salarySlip.value = slipRes.data;
    attendance.value = attRes.data;
    rosterOverview.value = rosterRes.data;
  } catch (err) {
    ElMessage.error("获取财务数据失败");
  }
};

const formatHours = (hours) => {
  if (!hours || hours <= 0) return "0 小时";
  return `${Number(hours).toFixed(1)} 小时`;
};

const formatNumber = (v) => Number(v || 0).toFixed(2);

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

.pkg-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  line-height: 18px;
}

.pkg-name {
  color: #333;
}

.pkg-count,
.pkg-amount {
  color: #666;
}

.muted {
  color: #999;
}
</style>
