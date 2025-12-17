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

    <el-row :gutter="16">
      <el-col :span="10">
        <el-card class="expenses-card">
          <h3>新增支出</h3>
          <el-form :model="expenseForm" label-width="80px" label-position="top" class="expense-form">
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
            <el-form-item label="备注">
              <el-input v-model="expenseForm.note" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" block :loading="creatingExpense" @click="createExpense">
                新增支出
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card>
          <div class="history-header">
            <h3>支出历史</h3>
            <div class="history-actions">
              <el-date-picker
                v-model="selectedMonth"
                type="month"
                placeholder="选择月份"
                value-format="YYYY-MM"
                @change="reload"
              />
              <el-button @click="reload">刷新</el-button>
            </div>
          </div>
          <el-table :data="expenses" border style="width: 100%">
            <el-table-column prop="expense_date" label="日期" width="120" />
            <el-table-column prop="title" label="标题" />
            <el-table-column prop="amount" label="金额" />
            <el-table-column prop="note" label="备注" />
            <el-table-column label="操作" width="180" align="center">
              <template #default="{ row }">
                <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="confirmDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="editDialogVisible" title="编辑支出" width="480px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="日期">
          <el-date-picker
            v-model="editForm.expense_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择日期"
          />
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="editForm.title" />
        </el-form-item>
        <el-form-item label="金额">
          <el-input v-model.number="editForm.amount" type="number" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="editForm.note" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="editingExpense" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import dayjs from "dayjs";
import api from "../api/client";

const selectedMonth = ref(dayjs().format("YYYY-MM"));
const expenses = ref([]);
const creatingExpense = ref(false);
const expenseForm = reactive({
  expense_date: dayjs().format("YYYY-MM-DD"),
  title: "",
  amount: null,
  note: ""
});

const editDialogVisible = ref(false);
const editingExpense = ref(false);
const editingId = ref(null);
const editForm = reactive({
  expense_date: dayjs().format("YYYY-MM-DD"),
  title: "",
  amount: null,
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
    resetCreateForm();
    await fetchExpenses();
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || "新增支出失败");
  } finally {
    creatingExpense.value = false;
  }
};

const openEdit = (row) => {
  editingId.value = row.id;
  editForm.expense_date = row.expense_date;
  editForm.title = row.title;
  editForm.amount = row.amount;
  editForm.note = row.note || "";
  editDialogVisible.value = true;
};

const submitEdit = async () => {
  if (!editingId.value) return;
  if (!editForm.title || !editForm.amount || !editForm.expense_date) {
    ElMessage.warning("请填写支出的日期、标题和金额");
    return;
  }
  editingExpense.value = true;
  try {
    await api.put(`/expenses/${editingId.value}`, editForm);
    ElMessage.success("更新支出成功");
    editDialogVisible.value = false;
    await fetchExpenses();
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || "更新支出失败");
  } finally {
    editingExpense.value = false;
  }
};

const confirmDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认删除支出【${row.title}】吗？`,
      "删除确认",
      {
        type: "warning",
        confirmButtonText: "删除",
        cancelButtonText: "取消"
      }
    );
  } catch {
    return; // 用户取消
  }

  try {
    await api.delete(`/expenses/${row.id}`);
    ElMessage.success("已删除支出");
    await fetchExpenses();
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || "删除支出失败");
  }
};

const resetCreateForm = () => {
  expenseForm.expense_date = dayjs().format("YYYY-MM-DD");
  expenseForm.title = "";
  expenseForm.amount = null;
  expenseForm.note = "";
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
