<template>
  <div>
    <div class="toolbar">
      <div class="left">
        <h3>其他支出管理</h3>
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

    <el-card class="expenses-card">
      <h3>新增支出</h3>
      <el-form :model="expenseForm" inline label-width="80px" class="expense-form">
        <el-form-item label="日期">
          <el-date-picker
            v-model="expenseForm.expense_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择日期"
          />
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="expenseForm.title" placeholder="如 房租 / 水电" />
        </el-form-item>
        <el-form-item label="金额">
          <el-input v-model.number="expenseForm.amount" type="number" />
        </el-form-item>
        <el-form-item label="类别">
          <el-input v-model="expenseForm.category" placeholder="可选，如 rent" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="expenseForm.note" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="creatingExpense" @click="createExpense">
            新增支出
          </el-button>
        </el-form-item>
      </el-form>

      <el-table :data="expenses" border style="width: 100%">
        <el-table-column prop="expense_date" label="日期" width="120" />
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="amount" label="金额" />
        <el-table-column prop="category" label="类别" />
        <el-table-column prop="note" label="备注" />
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
const expenses = ref([]);
const creatingExpense = ref(false);
const expenseForm = reactive({
  expense_date: dayjs().format("YYYY-MM-DD"),
  title: "",
  amount: null,
  category: "",
  note: ""
});

const fetchExpenses = async () => {
  try {
    const { data } = await api.get("/expenses", {
      params: { month: selectedMonth.value }
    });
    expenses.value = data;
  } catch (err) {
    ElMessage.error("获取支出列表失败");
  }
};

const reload = async () => {
  await fetchExpenses();
};

const createExpense = async () => {
  if (!expenseForm.title || !expenseForm.amount || !expenseForm.expense_date) {
    ElMessage.warning("请填写支出的日期、标题和金额");
    return;
  }
  creatingExpense.value = true;
  try {
    await api.post("/expenses", expenseForm);
    ElMessage.success("新增支出成功");
    await fetchExpenses();
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || "新增支出失败");
  } finally {
    creatingExpense.value = false;
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

.expenses-card {
  margin-top: 0;
}
</style>

