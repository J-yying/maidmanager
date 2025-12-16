<template>
  <div>
    <div class="toolbar">
      <h3>历史订单</h3>
      <div class="toolbar-right">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          @change="fetchOrders"
        />
        <el-button type="primary" @click="fetchOrders">刷新</el-button>
      </div>
    </div>
    <el-table :data="orders" border style="width: 100%">
      <el-table-column type="index" label="序号" width="70" />
      <el-table-column prop="staff_name" label="姓名" width="120" />
      <el-table-column prop="customer_name" label="客户名称" />
      <el-table-column prop="order_date" label="日期" width="120" />
      <el-table-column prop="created_at" label="订单创建日期" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column prop="start_datetime" label="开始时间" width="180" />
      <el-table-column prop="end_datetime" label="结束时间" width="180" />
      <el-table-column prop="package_name" label="套餐名称" />
      <el-table-column prop="total_amount" label="金额" width="100" />
      <el-table-column prop="extra_amount" label="额外金额" width="100" />
      <el-table-column prop="note" label="备注" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          {{ row.status === "completed" ? "已完成" : row.status === "cancelled" ? "已取消" : row.status }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button type="text" size="small" @click="openEdit(row)">编辑</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="editVisible" title="编辑订单" width="520px">
      <el-form :model="editForm" label-width="96px">
        <el-form-item label="员工">
          <span>{{ editForm.staff_name }}</span>
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker
            v-model="editForm.date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择日期"
          />
        </el-form-item>
        <el-form-item label="开始时间">
          <el-time-select
            v-model="editForm.startTime"
            start="12:00"
            step="00:30"
            end="24:00"
            placeholder="选择开始时间"
          />
        </el-form-item>
        <el-form-item label="时长(分钟)">
          <el-input-number v-model="editForm.duration" :min="30" :step="30" />
        </el-form-item>
        <el-form-item label="套餐">
          <el-select v-model="editForm.package_id" placeholder="选择套餐" clearable>
            <el-option
              v-for="p in packages"
              :key="p.id"
              :label="`${p.name}（${p.duration_minutes}分钟 ¥${p.price}）`"
              :value="p.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="额外金额">
          <el-input-number v-model="editForm.extra_amount" :min="0" :step="50" />
        </el-form-item>
        <el-form-item label="总金额">
          <el-input-number v-model="editForm.total_amount" :min="0" :step="50" />
        </el-form-item>
        <el-form-item label="客户名称">
          <el-input v-model="editForm.customer_name" />
        </el-form-item>
        <el-form-item label="支付方式">
          <el-select v-model="editForm.payment_method" placeholder="选择支付方式">
            <el-option label="微信" value="wechat" />
            <el-option label="支付宝" value="alipay" />
            <el-option label="现金" value="cash" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="editForm.status">
            <el-option label="已完成" value="completed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="editForm.note" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveEdit">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import dayjs from "dayjs";
import api from "../api/client";

const orders = ref([]);
const dateRange = ref([]);
const packages = ref([]);
const editVisible = ref(false);
const saving = ref(false);

const editForm = reactive({
  id: null,
  staff_name: "",
  date: "",
  startTime: "",
  duration: 60,
  customer_name: "",
  package_id: null,
  extra_amount: 0,
  total_amount: 0,
  payment_method: "",
  status: "completed",
  note: ""
});

const fetchOrders = async () => {
  try {
    const params = {};
    if (dateRange.value && dateRange.value.length === 2) {
      params.from_date = dateRange.value[0];
      params.to_date = dateRange.value[1];
    }
    const { data } = await api.get("/orders", { params });
    orders.value = data;
  } catch (err) {
    ElMessage.error("获取订单列表失败");
  }
};

const formatDateTime = (value) => {
  if (!value) return "";
  return dayjs(value).format("YYYY-MM-DD HH:mm:ss");
};

const fetchPackages = async () => {
  try {
    const { data } = await api.get("/packages");
    packages.value = data;
  } catch (err) {
    ElMessage.error("获取套餐列表失败");
  }
};

const openEdit = (row) => {
  editForm.id = row.id;
  editForm.staff_name = row.staff_name;
  editForm.date = row.order_date;
  editForm.startTime = dayjs(row.start_datetime).format("HH:mm");
  const start = dayjs(row.start_datetime);
  const end = dayjs(row.end_datetime);
  editForm.duration = end.diff(start, "minute") || 60;
  editForm.customer_name = row.customer_name || "";
  editForm.package_id = row.package_id || null;
  editForm.extra_amount = row.extra_amount || 0;
  editForm.total_amount = row.total_amount || 0;
  editForm.payment_method = row.payment_method || "";
  editForm.status = row.status || "completed";
  editForm.note = row.note || "";
  editVisible.value = true;
};

const saveEdit = async () => {
  if (!editForm.id || !editForm.date || !editForm.startTime) {
    ElMessage.warning("请填写日期和开始时间");
    return;
  }
  saving.value = true;
  try {
    const start = dayjs(
      `${editForm.date} ${editForm.startTime}:00`,
      "YYYY-MM-DD HH:mm:ss"
    );
    const end = start.add(editForm.duration || 60, "minute");
    const payload = {
      customer_name: editForm.customer_name || null,
      start_datetime: start.format("YYYY-MM-DD HH:mm:ss"),
      end_datetime: end.format("YYYY-MM-DD HH:mm:ss"),
      total_amount: editForm.total_amount,
      package_id: editForm.package_id,
      extra_amount: editForm.extra_amount,
      payment_method: editForm.payment_method || null,
      note: editForm.note || null,
      status: editForm.status
    };
    await api.put(`/orders/${editForm.id}`, payload);
    ElMessage.success("订单已更新，并按最新配置重新计算提成");
    editVisible.value = false;
    await fetchOrders();
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || "更新订单失败");
  } finally {
    saving.value = false;
  }
};

onMounted(() => {
  fetchOrders();
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

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
