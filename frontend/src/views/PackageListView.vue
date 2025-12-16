<template>
  <div>
    <div class="toolbar">
      <h3>套餐管理</h3>
      <el-button type="primary" @click="openCreate">新增套餐</el-button>
    </div>

    <el-table :data="packages" border style="width: 100%">
      <el-table-column type="index" label="序号" width="70" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="duration_minutes" label="时长(分钟)" width="120" />
      <el-table-column prop="price" label="金额" width="120" />
      <el-table-column
        prop="default_commission"
        label="默认提成金额"
        width="140"
      />
      <el-table-column prop="description" label="备注" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button type="text" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button type="text" size="small" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="480px">
      <el-form :model="form" label-width="96px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="如 60分钟标准" />
        </el-form-item>
        <el-form-item label="时长" required>
          <el-input-number v-model="form.duration_minutes" :min="30" :step="30" />
          <span class="suffix">分钟</span>
        </el-form-item>
        <el-form-item label="金额" required>
          <el-input-number v-model="form.price" :min="0" :step="50" />
        </el-form-item>
        <el-form-item label="默认提成">
          <el-input-number
            v-model="form.default_commission"
            :min="0"
            :step="50"
            placeholder="如 300，员工可在此基础上单独调整"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.description" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import api from "../api/client";

const packages = ref([]);
const dialogVisible = ref(false);
const saving = ref(false);
const editingId = ref(null);

const form = reactive({
  name: "",
  duration_minutes: 60,
  price: 600,
  default_commission: 0,
  description: ""
});

const dialogTitle = computed(() =>
  editingId.value ? "编辑套餐" : "新增套餐"
);

const fetchPackages = async () => {
  try {
    const { data } = await api.get("/packages");
    packages.value = data;
  } catch (err) {
    ElMessage.error("获取套餐列表失败");
  }
};

const resetForm = () => {
  form.name = "";
  form.duration_minutes = 60;
  form.price = 600;
  form.default_commission = 0;
  form.description = "";
  editingId.value = null;
};

const openCreate = () => {
  resetForm();
  dialogVisible.value = true;
};

const openEdit = (row) => {
  editingId.value = row.id;
  form.name = row.name;
  form.duration_minutes = row.duration_minutes;
  form.price = row.price;
  form.default_commission = row.default_commission ?? 0;
  form.description = row.description || "";
  dialogVisible.value = true;
};

const save = async () => {
  if (!form.name || !form.duration_minutes || !form.price) {
    ElMessage.warning("请填写名称、时长和金额");
    return;
  }
  saving.value = true;
  try {
    if (editingId.value) {
      await api.put(`/packages/${editingId.value}`, form);
      ElMessage.success("更新套餐成功");
    } else {
      await api.post("/packages", form);
      ElMessage.success("新增套餐成功");
    }
    dialogVisible.value = false;
    await fetchPackages();
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || "保存失败");
  } finally {
    saving.value = false;
  }
};

const remove = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定删除套餐「${row.name}」吗？`,
      "提示",
      {
        type: "warning",
        confirmButtonText: "删除",
        cancelButtonText: "取消"
      }
    );
  } catch {
    return;
  }
  try {
    await api.delete(`/packages/${row.id}`);
    ElMessage.success("删除成功");
    await fetchPackages();
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || "删除失败");
  }
};

onMounted(() => {
  fetchPackages();
});
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.suffix {
  margin-left: 4px;
  font-size: 12px;
  color: #666;
}
</style>
