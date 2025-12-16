<template>
  <div>
    <div class="toolbar">
      <div class="left">
        <h3>工作管理</h3>
        <el-date-picker
          v-model="selectedDate"
          type="date"
          placeholder="选择日期"
          value-format="YYYY-MM-DD"
          @change="onDateChange"
        />
      </div>
      <div class="right">
        <el-button type="primary" @click="fetchDaySchedules">刷新日历</el-button>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :span="10">
        <el-card class="form-card">
          <h4>预约创建</h4>
          <el-form :model="form" label-width="96px">
            <el-form-item label="开始时间">
              <el-time-select
                v-model="form.startTime"
                start="12:00"
                step="00:30"
                end="24:00"
                placeholder="请选择开始时间（整点或半点）"
              />
            </el-form-item>
            <el-form-item label="套餐">
              <el-select
                v-model="selectedPackageId"
                placeholder="选择套餐"
                @change="onPackageChange"
              >
                <el-option
                  v-for="p in packages"
                  :key="p.id"
                  :label="`${p.name}（${p.duration_minutes}分钟 ¥${p.price}）`"
                  :value="p.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="客户名称">
              <el-input v-model="form.customer_name" placeholder="如 王总" />
            </el-form-item>
            <el-form-item label="备注">
              <el-input v-model="form.note" type="textarea" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="loadingAvailable" @click="loadAvailable">
                查询可用员工
              </el-button>
            </el-form-item>
          </el-form>

          <div v-if="availableStaff.length">
            <h4>可用员工</h4>
            <el-table
              :data="availableStaff"
              border
              style="width: 100%"
              @row-click="selectStaff"
              highlight-current-row
            >
              <el-table-column prop="id" label="ID" width="60" />
              <el-table-column prop="name" label="姓名" />
              <el-table-column label="提成方式">
                <template #default="{ row }">
                  <span v-if="row.commission_type === 'percentage'">比例提成</span>
                  <span v-else-if="row.commission_type === 'fixed'">固定金额</span>
                  <span v-else>/</span>
                </template>
              </el-table-column>
            </el-table>
            <div class="selected" v-if="selectedStaff">
              已选择员工：{{ selectedStaff.name }}（ID: {{ selectedStaff.id }}）
            </div>
            <el-button
              type="success"
              :disabled="!selectedStaff || !selectedPackageId"
              :loading="creatingOrder"
              @click="createOrder"
            >
              创建预约
            </el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card class="active-card">
          <h4>待处理订单</h4>
          <el-tabs v-model="activeTab">
            <el-tab-pane label="全部" name="all">
              <el-table :data="activeOrders" border style="width: 100%">
                <el-table-column prop="staff_name" label="员工" width="100" />
                <el-table-column prop="customer_name" label="客户" />
                <el-table-column prop="start_datetime" label="开始时间" />
                <el-table-column prop="end_datetime" label="结束时间" />
                <el-table-column prop="package_name" label="套餐" />
                <el-table-column prop="status" label="状态" width="80">
                  <template #default="{ row }">
                    {{ row.status === "pending"
                      ? "待开始"
                      : row.status === "in_progress"
                      ? "进行中"
                      : row.status === "finished"
                      ? "待结算"
                      : row.status }}
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
            <el-tab-pane label="待开始" name="pending">
              <el-table :data="pendingOrders" border style="width: 100%">
                <el-table-column prop="staff_name" label="员工" width="100" />
                <el-table-column prop="customer_name" label="客户" />
                <el-table-column prop="start_datetime" label="预约开始时间" />
                <el-table-column prop="package_name" label="套餐" />
                <el-table-column label="操作" width="140">
                  <template #default="{ row }">
                    <el-button type="text" size="small" @click="startOrder(row)">
                      开始
                    </el-button>
                    <el-button type="text" size="small" @click="cancelOrder(row)">
                      取消
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
            <el-tab-pane label="进行中" name="in_progress">
              <el-table :data="inProgressOrders" border style="width: 100%">
                <el-table-column prop="staff_name" label="员工" width="100" />
                <el-table-column prop="customer_name" label="客户" />
                <el-table-column prop="start_datetime" label="实际开始时间" />
                <el-table-column prop="end_datetime" label="预计结束时间" />
                <el-table-column prop="package_name" label="套餐" />
                <el-table-column label="操作" width="120">
                  <template #default="{ row }">
                    <el-button type="text" size="small" @click="finishOrder(row)">
                      结束服务
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
            <el-tab-pane label="待结算" name="finished">
              <el-table :data="finishedOrders" border style="width: 100%">
                <el-table-column prop="staff_name" label="员工" width="100" />
                <el-table-column prop="customer_name" label="客户" />
                <el-table-column prop="start_datetime" label="开始时间" />
                <el-table-column prop="end_datetime" label="结束时间" />
                <el-table-column prop="package_name" label="套餐" />
                <el-table-column label="操作" width="120">
                  <template #default="{ row }">
                    <el-button type="text" size="small" @click="openSettleDialog(row)">
                      结算
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="calendar-card">
      <div class="calendar-header">
        <span>当日排班与订单（{{ selectedDate }}）</span>
        <span class="calendar-legend">
          <span class="legend-box shift"></span> 在班
          <span class="legend-box order-active"></span> 待处理
          <span class="legend-box order-completed"></span> 已完结
        </span>
      </div>
      <div v-if="daySchedules.length">
        <el-table :data="daySchedules" border style="width: 100%">
          <el-table-column prop="staff_name" label="员工" width="80" />
          <el-table-column
            v-for="tick in timeTicks"
            :key="tick"
            :label="tick"
          >
            <template #default="{ row }">
              <div
                class="calendar-cell"
                :class="cellClass(row, tick)"
                @click="onCellClick(row, tick)"
              />
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div v-else class="empty-hint">该日暂无排班或订单</div>
    </el-card>

    <el-dialog
      v-model="settleDialogVisible"
      title="订单结算"
      width="480px"
    >
      <el-form :model="settleForm" label-width="96px">
        <el-form-item label="员工">
          <span>{{ settleForm.staff_name }}</span>
        </el-form-item>
        <el-form-item label="客户">
          <span>{{ settleForm.customer_name || "-" }}</span>
        </el-form-item>
        <el-form-item label="套餐">
          <span>{{ settleForm.package_name || "-" }}</span>
        </el-form-item>
        <el-form-item label="实收金额" required>
          <el-input-number v-model="settleForm.total_amount" :min="0" :step="50" />
        </el-form-item>
        <el-form-item label="支付方式" required>
          <el-select v-model="settleForm.payment_method" placeholder="选择支付方式">
            <el-option label="微信" value="wechat" />
            <el-option label="支付宝" value="alipay" />
            <el-option label="现金" value="cash" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="settleForm.note" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="settleDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="settling" @click="settleOrder">
          确认结算
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import dayjs from "dayjs";
import api from "../api/client";

const selectedDate = ref(dayjs().format("YYYY-MM-DD"));

const form = reactive({
  startTime: "",
  duration: 60,
  customer_name: "",
  total_amount: 600,
  payment_method: "wechat",
  extra_amount: 0,
  note: ""
});

const availableStaff = ref([]);
const loadingAvailable = ref(false);
const selectedStaffId = ref(null);
const creatingOrder = ref(false);
const daySchedules = ref([]);

const packages = ref([]);
const selectedPackageId = ref(null);

const timeTicks = [
  "12:00",
  "13:00",
  "14:00",
  "15:00",
  "16:00",
  "17:00",
  "18:00",
  "19:00",
  "20:00",
  "21:00",
  "22:00",
  "23:00",
  "24:00"
];
const dayStartMinutes = 12 * 60;
const dayEndMinutes = 24 * 60;
const daySpan = dayEndMinutes - dayStartMinutes;

const selectedStaff = computed(() =>
  availableStaff.value.find((s) => s.id === selectedStaffId.value)
);

const selectedPackage = computed(() =>
  packages.value.find((p) => p.id === selectedPackageId.value)
);

const activeTab = ref("all");
const activeOrders = ref([]);

const pendingOrders = computed(() =>
  activeOrders.value.filter((o) => o.status === "pending")
);
const inProgressOrders = computed(() =>
  activeOrders.value.filter((o) => o.status === "in_progress")
);
const finishedOrders = computed(() =>
  activeOrders.value.filter((o) => o.status === "finished")
);

const buildStartDateTime = () =>
  `${selectedDate.value} ${form.startTime}:00`;

const onDateChange = () => {
  if (!selectedDate.value) return;
  fetchDaySchedules();
};

const timeStrToMinutes = (timeStr) => {
  const [h, m] = timeStr.split(":");
  return Number(h || 0) * 60 + Number(m || 0);
};

const dtStrToMinutes = (dtStr) => {
  const [, timePart] = dtStr.split(" ");
  return timeStrToMinutes(timePart || "00:00");
};

const styleForShift = (shift) => {
  const startM = Math.max(timeStrToMinutes(shift.start_time), dayStartMinutes);
  const endM = Math.min(timeStrToMinutes(shift.end_time), dayEndMinutes);
  if (endM <= startM) return { display: "none" };
  const left = ((startM - dayStartMinutes) / daySpan) * 100;
  const width = ((endM - startM) / daySpan) * 100;
  return {
    left: `${left}%`,
    width: `${width}%`
  };
};

const styleForOrder = (order) => {
  const startM = Math.max(dtStrToMinutes(order.start_datetime), dayStartMinutes);
  const endM = Math.min(dtStrToMinutes(order.end_datetime), dayEndMinutes);
  if (endM <= startM) return { display: "none" };
  const left = ((startM - dayStartMinutes) / daySpan) * 100;
  const width = ((endM - startM) / daySpan) * 100;
  return {
    left: `${left}%`,
    width: `${width}%`
  };
};

const cellClass = (row, tick) => {
  const [h] = tick.split(":");
  const startM = Number(h || 0) * 60;
  const endM = startM + 60;

  const overlapsShift = (startMin, endMin) =>
    row.shifts.some((sh) => {
      const s = timeStrToMinutes(sh.start_time);
      const e = timeStrToMinutes(sh.end_time);
      return s < endMin && e > startMin;
    });

  const overlapsOrders = (ordersArr, statuses) =>
    ordersArr.some((o) => {
      if (statuses && !statuses.includes(o.status)) return false;
      const s = dtStrToMinutes(o.start_datetime);
      const e = dtStrToMinutes(o.end_datetime);
      return s < endM && e > startM;
    });

  const inShift = overlapsShift(startM, endM);
  const hasPending = overlapsOrders(row.pending_orders || [], null);
  const hasActive = overlapsOrders(row.orders || [], ["in_progress", "finished"]);
  const hasCompleted = overlapsOrders(row.orders || [], ["completed"]);

  if (!inShift && !hasPending && !hasActive && !hasCompleted) return "cell-empty";
  if (hasActive) return "cell-active";
  if (hasPending) return "cell-pending";
  if (hasCompleted) return "cell-completed";
  if (inShift) return "cell-shift";
  return "cell-empty";
};

const onCellClick = (row, tick) => {
  const [h] = tick.split(":");
  const hh = h.padStart(2, "0");
  form.startTime = `${hh}:00`;
  selectedStaffId.value = row.staff_id;
  loadAvailable();
};

const onTimelineClick = (event, row) => {
  const container = event.currentTarget;
  const rect = container.getBoundingClientRect();
  if (!rect.width) return;
  const ratio = (event.clientX - rect.left) / rect.width;
  let minutes = dayStartMinutes + ratio * daySpan;
  // 四舍五入到最近的半小时
  const halfSteps = Math.round(minutes / 30);
  minutes = halfSteps * 30;
  if (minutes < dayStartMinutes) minutes = dayStartMinutes;
  if (minutes > dayEndMinutes - 30) minutes = dayEndMinutes - 30;

  const hour = Math.floor(minutes / 60);
  const minute = minutes % 60;
  const timeStr = `${hour.toString().padStart(2, "0")}:${minute
    .toString()
    .padStart(2, "0")}:00`;

  // 更新开单时间为点击的时间点（仅更新时分）
  form.startTime = timeStr.slice(0, 5);

  // 自动查询可用员工，并尝试选中当前行员工
  loadAvailable().then(() => {
    const found = availableStaff.value.find((s) => s.id === row.staff_id);
    if (found) {
      selectedStaffId.value = row.staff_id;
    } else {
      ElMessage.info("该时间该员工可能已有订单或未排班");
    }
  });
};

const onPackageChange = () => {
  const pkg = selectedPackage.value;
  if (!pkg) {
    form.extra_amount = 0;
    return;
  }
  form.duration = pkg.duration_minutes;
  form.extra_amount = 0;
  form.total_amount = pkg.price;
};

const onExtraAmountChange = () => {
  const pkg = selectedPackage.value;
  if (!pkg) return;
  const extra = form.extra_amount || 0;
  form.total_amount = pkg.price + extra;
};

const loadAvailable = async () => {
  if (!form.startTime || !selectedPackageId.value) {
    ElMessage.warning("请先选择开始时间和套餐");
    return;
  }
  loadingAvailable.value = true;
  try {
    const { data } = await api.get("/available_staff", {
      params: {
        target_time: buildStartDateTime(),
        duration: selectedPackage.value?.duration_minutes || 60
      }
    });
    availableStaff.value = data;
    if (!data.length) {
      ElMessage.info("该时间段暂无可用员工");
    }
    selectedStaffId.value = null;
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || "查询可用员工失败");
  } finally {
    loadingAvailable.value = false;
  }
};

const selectStaff = (row) => {
  selectedStaffId.value = row.id;
};

const createOrder = async () => {
  if (!selectedStaff.value) {
    ElMessage.warning("请先选择员工");
    return;
  }
  creatingOrder.value = true;
  try {
    const start = dayjs(buildStartDateTime(), "YYYY-MM-DD HH:mm:ss");
    const duration = selectedPackage.value?.duration_minutes || 60;
    const end = start.add(duration, "minute");
    const pkg = selectedPackage.value;
    const noteParts = [];
    if (pkg) {
      const pkgText = `套餐：${pkg.name}（${pkg.duration_minutes}分钟 ¥${pkg.price}）`;
      noteParts.push(pkgText);
    }
    if (form.note) {
      noteParts.push(form.note);
    }
    const note = noteParts.length ? noteParts.join(" | ") : null;

    const payload = {
      staff_id: selectedStaff.value.id,
      customer_name: form.customer_name || null,
      start_datetime: start.format("YYYY-MM-DD HH:mm:ss"),
      end_datetime: end.format("YYYY-MM-DD HH:mm:ss"),
      total_amount: pkg ? pkg.price : 0,
      package_id: selectedPackageId.value,
      extra_amount: 0,
      payment_method: null,
      note
    };
    await api.post("/orders", payload);
    ElMessage.success("预约已创建");
    await fetchActiveOrders();
    fetchDaySchedules();
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || "创建订单失败");
  } finally {
    creatingOrder.value = false;
  }
};

const fetchDaySchedules = async () => {
  try {
    const { data } = await api.get("/orders/day_view", {
      params: { date: selectedDate.value }
    });
    daySchedules.value = data;
  } catch (err) {
    ElMessage.error("获取日历数据失败");
  }
};

const fetchPackages = async () => {
  try {
    const { data } = await api.get("/packages");
    packages.value = data;
  } catch (err) {
    ElMessage.error("获取套餐列表失败");
  }
};

const fetchActiveOrders = async () => {
  try {
    const { data } = await api.get("/orders/active", {
      params: { date: selectedDate.value }
    });
    activeOrders.value = data;
  } catch (err) {
    ElMessage.error("获取待处理订单失败");
  }
};

const startOrder = async (row) => {
  try {
    const now = dayjs();
    const start = now;
    const pkg = packages.value.find((p) => p.id === row.package_id);
    const duration = pkg?.duration_minutes || 60;
    const end = start.add(duration, "minute");
    const payload = {
      start_datetime: start.format("YYYY-MM-DD HH:mm:ss"),
      end_datetime: end.format("YYYY-MM-DD HH:mm:ss"),
      status: "in_progress"
    };
    await api.put(`/orders/${row.id}`, payload);
    ElMessage.success("订单已开始");
    await fetchActiveOrders();
    await fetchDaySchedules();
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || "开始订单失败");
  }
};

const cancelOrder = async (row) => {
  try {
    await ElMessageBox.confirm("确定要取消该订单吗？", "确认取消", {
      type: "warning",
      confirmButtonText: "取消订单",
      cancelButtonText: "返回"
    });
  } catch {
    return;
  }
  try {
    await api.put(`/orders/${row.id}`, { status: "cancelled" });
    ElMessage.success("订单已取消");
    await fetchActiveOrders();
    await fetchDaySchedules();
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || "取消订单失败");
  }
};

const finishOrder = async (row) => {
  try {
    const now = dayjs();
    const payload = {
      end_datetime: now.format("YYYY-MM-DD HH:mm:ss"),
      status: "finished"
    };
    await api.put(`/orders/${row.id}`, payload);
    ElMessage.success("服务已结束");
    await fetchActiveOrders();
    await fetchDaySchedules();
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || "结束订单失败");
  }
};

const settleDialogVisible = ref(false);
const settleForm = reactive({
  id: null,
  staff_name: "",
  customer_name: "",
  package_name: "",
  total_amount: 0,
  payment_method: "",
  note: ""
});
const settling = ref(false);

const openSettleDialog = (row) => {
  settleForm.id = row.id;
  settleForm.staff_name = row.staff_name;
  settleForm.customer_name = row.customer_name || "";
  settleForm.package_name = row.package_name || "";
  settleForm.total_amount = row.total_amount || 0;
  settleForm.payment_method = row.payment_method || "";
  settleForm.note = row.note || "";
  settleDialogVisible.value = true;
};

const settleOrder = async () => {
  if (!settleForm.id) return;
  if (!settleForm.total_amount || !settleForm.payment_method) {
    ElMessage.warning("请填写实收金额和支付方式");
    return;
  }
  settling.value = true;
  try {
    const payload = {
      total_amount: settleForm.total_amount,
      payment_method: settleForm.payment_method,
      note: settleForm.note || null,
      status: "completed"
    };
    await api.put(`/orders/${settleForm.id}`, payload);
    ElMessage.success("订单已结算");
    settleDialogVisible.value = false;
    await fetchActiveOrders();
    await fetchDaySchedules();
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || "结算订单失败");
  } finally {
    settling.value = false;
  }
};

const notifiedTimeoutIds = new Set();
let timeoutTimer = null;

const checkTimeouts = () => {
  const now = dayjs();
  inProgressOrders.value.forEach((order) => {
    const end = dayjs(order.end_datetime);
    if (!end.isValid()) return;
    if (now.isAfter(end) && !notifiedTimeoutIds.has(order.id)) {
      notifiedTimeoutIds.add(order.id);
      ElMessage.warning(
        `订单已到时间：${order.staff_name || ""} - ${order.customer_name || ""}`
      );
    }
  });
};

onMounted(() => {
  fetchDaySchedules();
  fetchPackages();
  fetchActiveOrders();
  timeoutTimer = setInterval(checkTimeouts, 30000);
});

onUnmounted(() => {
  if (timeoutTimer) {
    clearInterval(timeoutTimer);
  }
});
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.toolbar .left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.form-card {
  margin-bottom: 16px;
}

.calendar-card {
  margin-top: 16px;
}

.selected {
  margin: 12px 0;
}

.extra-hint {
  margin-left: 8px;
  font-size: 12px;
  color: #999;
}

.suffix {
  margin-left: 4px;
  font-size: 12px;
  color: #666;
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.calendar-legend {
  font-size: 12px;
  color: #666;
}

.legend-box {
  display: inline-block;
  width: 14px;
  height: 6px;
  border-radius: 3px;
  margin: 0 4px;
}

.legend-box.shift {
  background: rgba(82, 196, 26, 0.6);
}

.legend-box.order-active {
  background: rgba(245, 34, 45, 0.8);
}

.legend-box.order-completed {
  background: rgba(24, 144, 255, 0.8);
}

.time-scale {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #999;
  margin: 0 0 8px 90px;
}

.time-scale .tick {
  width: 1px;
}

.day-rows {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.bar {
  position: absolute;
  top: 4px;
  bottom: 4px;
  border-radius: 4px;
}

.shift-bar {
  background: rgba(82, 196, 26, 0.35);
}

.order-bar-active {
  background: rgba(245, 34, 45, 0.8);
}

.order-bar-completed {
  background: rgba(24, 144, 255, 0.8);
}

.empty-hint {
  font-size: 13px;
  color: #999;
}
</style>
