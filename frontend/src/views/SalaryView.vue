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
        <el-table-column label="套餐提成明细" min-width="220">
          <template #default="{ row }">
            <div v-if="row.packages && row.packages.length" class="pkg-list">
              <div
                v-for="p in row.packages"
                :key="`${row.staff_id}-${p.package_id || 'none'}-${p.order_count}`"
                class="pkg-row"
              >
                <span class="pkg-name">{{ p.package_name || "未指定套餐" }}</span>
                <span class="pkg-count">×{{ p.order_count }}</span>
                <span class="pkg-commission">提成￥{{ formatNumber(p.total_commission) }}</span>
              </div>
            </div>
            <span v-else class="muted">-</span>
          </template>
        </el-table-column>
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

const formatNumber = (v) => Number(v || 0).toFixed(2);

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

.pkg-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.pkg-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.pkg-name {
  color: #333;
}

.pkg-count {
  color: #666;
}

.pkg-commission {
  color: #409eff;
}

.muted {
  color: #999;
}
</style>
