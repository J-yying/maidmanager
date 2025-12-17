<template>
  <div>
    <div class="toolbar">
      <el-button type="primary" @click="openCreate">新增员工</el-button>
      <el-select v-model="statusFilter" placeholder="员工状态" clearable @change="fetchStaff">
        <el-option label="在职" value="active" />
        <el-option label="离职" value="resigned" />
      </el-select>
    </div>
    <el-table :data="staffList" border style="width: 100%">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="姓名" />
      <el-table-column prop="phone" label="电话" />
      <el-table-column label="状态">
        <template #default="{ row }">
          {{ row.status === "active" ? "在职" : row.status === "resigned" ? "离职" : row.status }}
        </template>
      </el-table-column>
      <el-table-column prop="base_salary" label="底薪" />
      <el-table-column label="提成方式">
        <template #default="{ row }">
          <span v-if="row.commission_type === 'percentage'">比例提成</span>
          <span v-else-if="row.commission_type === 'fixed'">固定金额</span>
          <span v-else>/</span>
        </template>
      </el-table-column>
      <el-table-column label="提成数值">
        <template #default="{ row }">
          <span v-if="row.commission_value">
            <template v-if="row.commission_type === 'percentage'">
              {{ (row.commission_value * 100).toFixed(0) }}%
            </template>
            <template v-else>
              {{ row.commission_value }}
            </template>
          </span>
          <span v-else>/</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button type="text" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button
            v-if="row.commission_type === 'fixed'"
            type="text"
            size="small"
            @click="openCommissionDialog(row)"
          >
            套餐提成
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑员工' : '新增员工'" width="480px">
      <el-form :model="form" label-width="96px">
        <el-form-item label="姓名" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status">
            <el-option label="在职" value="active" />
            <el-option label="离职" value="resigned" />
          </el-select>
        </el-form-item>
        <el-form-item label="底薪">
          <el-input v-model.number="form.base_salary" type="number" />
        </el-form-item>
        <el-form-item label="提成类型">
          <el-select v-model="form.commission_type">
            <el-option label="比例提成" value="percentage" />
            <el-option label="固定金额" value="fixed" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.commission_type === 'percentage'" label="提成比例">
          <el-input v-model.number="form.commission_value" type="number" placeholder="如 50 表示 50%" :step="1" :min="0">
            <template #append>%</template>
          </el-input>
        </el-form-item>
        <el-form-item v-else label="提成说明">
          <span class="hint">固定金额模式下，请在“套餐提成”中为每个套餐配置提成金额。</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">
          保存
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="commissionDialogVisible"
      :title="commissionStaff ? `套餐提成配置 - ${commissionStaff.name}` : '套餐提成配置'"
      width="640px"
    >
      <el-table
        v-loading="commissionLoading"
        :data="commissionRows"
        border
        style="width: 100%"
      >
        <el-table-column prop="package_name" label="套餐名称" />
        <el-table-column prop="default_commission" label="默认提成" width="120" />
        <el-table-column label="员工提成" width="160">
          <template #default="{ row }">
            <el-input-number
              v-model="row.staff_commission"
              :min="0"
              :step="50"
              placeholder="不填则使用默认"
            />
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="commissionDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="commissionSaving" @click="saveCommission">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import api from "../api/client";

const staffList = ref([]);
const statusFilter = ref();
const dialogVisible = ref(false);
const submitting = ref(false);
const isEdit = ref(false);
const editingId = ref(null);

const form = reactive({
  name: "",
  phone: "",
  status: "active",
  base_salary: 0,
  commission_type: "percentage",
  commission_value: 0 // UI 层使用百分比数值，如 50 表示 50%
});

const fetchStaff = async () => {
  try {
    const params = {};
    if (statusFilter.value) {
      params.status = statusFilter.value;
    }
    const { data } = await api.get("/staff", { params });
    staffList.value = data;
  } catch (err) {
    ElMessage.error("获取员工列表失败");
  }
};

const resetForm = () => {
  form.name = "";
  form.phone = "";
  form.status = "active";
  form.base_salary = 0;
  form.commission_type = "percentage";
  form.commission_value = 0;
};

const openCreate = () => {
  isEdit.value = false;
  editingId.value = null;
  resetForm();
  dialogVisible.value = true;
};

const openEdit = (row) => {
  isEdit.value = true;
  editingId.value = row.id;
  form.name = row.name;
  form.phone = row.phone || "";
  form.status = row.status || "active";
  form.base_salary = row.base_salary ?? 0;
  form.commission_type = row.commission_type || "percentage";
  if (form.commission_type === "percentage") {
    form.commission_value = ((row.commission_value ?? 0) * 100).toFixed(0) * 1;
  } else {
    form.commission_value = row.commission_value ?? 0;
  }
  dialogVisible.value = true;
};

const commissionDialogVisible = ref(false);
const commissionLoading = ref(false);
const commissionSaving = ref(false);
const commissionStaff = ref(null);
const commissionRows = ref([]);

const openCommissionDialog = async (row) => {
  commissionStaff.value = row;
  commissionDialogVisible.value = true;
  commissionLoading.value = true;
  try {
    const { data } = await api.get(`/staff/${row.id}/package_commissions`);
    commissionRows.value = data;
  } catch (err) {
    ElMessage.error("获取套餐提成配置失败");
  } finally {
    commissionLoading.value = false;
  }
};

const saveCommission = async () => {
  if (!commissionStaff.value) return;
  commissionSaving.value = true;
  try {
    const payload = commissionRows.value
      .filter((row) => row.staff_commission != null)
      .map((row) => ({
        package_id: row.package_id,
        commission_amount: row.staff_commission
      }));
    await api.put(`/staff/${commissionStaff.value.id}/package_commissions`, payload);
    ElMessage.success("套餐提成配置已保存");
    commissionDialogVisible.value = false;
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || "保存套餐提成失败");
  } finally {
    commissionSaving.value = false;
  }
};

const submitForm = async () => {
  if (!form.name) {
    ElMessage.warning("请填写姓名");
    return;
  }
  submitting.value = true;
  try {
    const payload = {
      name: form.name,
      phone: form.phone,
      status: form.status,
      base_salary: form.base_salary,
      commission_type: form.commission_type,
      commission_value:
        form.commission_type === "percentage"
          ? (form.commission_value || 0) / 100
          : form.commission_value || 0
    };

    if (isEdit.value && editingId.value != null) {
      await api.put(`/staff/${editingId.value}`, payload);
      ElMessage.success("更新成功");
    } else {
      await api.post("/staff", payload);
      ElMessage.success("新增成功");
    }
    dialogVisible.value = false;
    fetchStaff();
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || "保存失败");
  } finally {
    submitting.value = false;
  }
};

onMounted(() => {
  fetchStaff();
});
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.hint {
  font-size: 12px;
  color: #999;
}
</style>
