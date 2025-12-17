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
              <el-time-picker
                v-model="form.startTime"
                format="HH:mm"
                value-format="HH:mm"
                placeholder="请选择开始时间"
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
          <h4>当日订单</h4>
          <el-tabs v-model="activeTab">
            <el-tab-pane label="当日订单" name="all">
              <el-table :data="activeOrders" border style="width: 100%">
                <el-table-column prop="staff_name" label="员工" width="100" />
                <el-table-column prop="customer_name" label="客户" />
                <el-table-column prop="start_datetime" label="开始时间" />
                <el-table-column prop="end_datetime" label="结束时间" />
                <el-table-column prop="package_name" label="套餐" />
                <el-table-column prop="status" label="状态" width="80">
                  <template #default="{ row }">
                    {{ statusLabel(row.status) }}
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
                    <el-button type="text" size="small" @click="openStartDialog(row)">
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
                <el-table-column label="操作" width="200">
                  <template #default="{ row }">
                    <el-button type="text" size="small" @click="openExtendDialog(row)">
                      续钟
                    </el-button>
                    <el-button type="text" size="small" @click="openFinishDialog(row)">
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
            <el-tab-pane label="已完成（当日）" name="completed">
              <el-table :data="completedOrders" border style="width: 100%">
                <el-table-column prop="staff_name" label="员工" width="100" />
                <el-table-column prop="customer_name" label="客户" />
                <el-table-column prop="start_datetime" label="开始时间" />
                <el-table-column prop="end_datetime" label="结束时间" />
                <el-table-column prop="package_name" label="套餐" />
                <el-table-column prop="total_amount" label="实收金额" />
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
          <span class="legend-box pending"></span> 待开始
          <span class="legend-box active"></span> 进行中
          <span class="legend-box completed"></span> 已完成
        </span>
      </div>
      <div v-if="daySchedules.length" class="timeline-wrapper">
        <div class="timeline-scale">
          <span class="scale-label">员工</span>
          <div class="scale-bar">
            <span
              v-for="tick in timeTicks"
              :key="tick"
              class="scale-tick"
              :style="{ left: tickLeft(tick) }"
            >
              {{ tick }}
            </span>
          </div>
        </div>
        <div
          v-for="row in daySchedules"
          :key="row.staff_id"
          class="timeline-row"
        >
          <div class="staff-col">{{ row.staff_name }}</div>
          <div class="timeline-track" @click="(e) => onTimelineClick(e, row)">
            <div
              v-for="shift in row.shifts"
              :key="`s-${shift.id}`"
              class="bar shift"
              :style="styleForShift(shift)"
            />
            <div
              v-for="order in row.pending_orders || []"
              :key="`p-${order.id}`"
              class="bar pending"
              :style="styleForOrder(order)"
            />
            <div
              v-for="order in (row.orders || []).filter((o) => ['in_progress', 'finished'].includes(o.status))"
              :key="`a-${order.id}`"
              class="bar active"
              :style="styleForOrder(order)"
            />
            <div
              v-for="order in (row.orders || []).filter((o) => o.status === 'completed')"
              :key="`c-${order.id}`"
              class="bar completed"
              :style="styleForOrder(order)"
            />
          </div>
        </div>
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
        <el-form-item label="实际开始">
          <el-time-picker
            v-model="settleForm.start_time"
            format="HH:mm"
            value-format="HH:mm"
            placeholder="请选择"
          />
        </el-form-item>
        <el-form-item label="实际结束">
          <el-time-picker
            v-model="settleForm.end_time"
            format="HH:mm"
            value-format="HH:mm"
            placeholder="请选择"
          />
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

    <el-dialog v-model="startDialogVisible" title="开始服务" width="400px">
      <el-form :model="startForm" label-width="100px">
        <el-form-item label="实际开始">
          <el-time-picker v-model="startForm.start_time" format="HH:mm" value-format="HH:mm" placeholder="选择开始时间" />
        </el-form-item>
        <el-form-item label="预计结束">
          <el-time-picker v-model="startForm.end_time" format="HH:mm" value-format="HH:mm" placeholder="选择预计结束" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="startDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitStart">确认开始</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="finishDialogVisible" title="结束服务" width="400px">
      <el-form :model="finishForm" label-width="100px">
        <el-form-item label="实际开始">
          <el-time-picker
            v-model="finishForm.start_time"
            format="HH:mm"
            value-format="HH:mm"
            placeholder="开始时间"
            disabled
          />
        </el-form-item>
        <el-form-item label="实际结束">
          <el-time-picker
            v-model="finishForm.end_time"
            format="HH:mm"
            value-format="HH:mm"
            placeholder="结束时间"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="finishDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitFinish">确认结束</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="extendDialogVisible" title="续钟" width="420px">
      <el-form :model="extendForm" label-width="100px">
        <el-form-item label="当前结束">
          <span>{{ extendForm.base_end || "-" }}</span>
        </el-form-item>
        <el-form-item label="续钟套餐">
          <el-select v-model="extendForm.package_id" placeholder="选择套餐" @change="updateExtendPreview">
            <el-option
              v-for="p in packages"
              :key="p.id"
              :value="p.id"
              :label="`${p.name}（${p.duration_minutes}分钟）`"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="预计结束">
          <span>{{ extendForm.preview_end || "-" }}</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="extendDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitExtend">确认续钟</el-button>
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

const timeTicks = ref(["12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00", "22:00", "23:00", "24:00"]);
const dayStartMinutes = ref(12 * 60);
const dayEndMinutes = ref(24 * 60);
const daySpan = computed(() => dayEndMinutes.value - dayStartMinutes.value);

const tickLeft = (tick) => {
  const mins = timeStrToMinutes(tick);
  const left = ((mins - dayStartMinutes.value) / daySpan.value) * 100;
  return `${left}%`;
};

const minutesToHHMM = (mins) => {
  const h = Math.floor(mins / 60)
    .toString()
    .padStart(2, "0");
  const m = (mins % 60).toString().padStart(2, "0");
  return `${h}:${m}`;
};

const timeSelectStart = computed(() => minutesToHHMM(dayStartMinutes.value));
const timeSelectEnd = computed(() => minutesToHHMM(dayEndMinutes.value));

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
const completedOrders = computed(() =>
  activeOrders.value.filter((o) => o.status === "completed")
);

const statusLabel = (status) => {
  const map = {
    pending: "待开始",
    in_progress: "进行中",
    finished: "待结算",
    completed: "已完成",
    cancelled: "已取消"
  };
  return map[status] || status;
};

const buildStartDateTime = () =>
  `${selectedDate.value} ${form.startTime}:00`;

const onDateChange = () => {
  if (!selectedDate.value) return;
  fetchDaySchedules();
  fetchActiveOrders();
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
  const startM = Math.max(timeStrToMinutes(shift.start_time), dayStartMinutes.value);
  const endM = Math.min(timeStrToMinutes(shift.end_time), dayEndMinutes.value);
  if (endM <= startM) return { display: "none" };
  const left = ((startM - dayStartMinutes.value) / daySpan.value) * 100;
  const width = ((endM - startM) / daySpan.value) * 100;
  return {
    left: `${left}%`,
    width: `${width}%`
  };
};

const styleForOrder = (order) => {
  const startM = Math.max(dtStrToMinutes(order.start_datetime), dayStartMinutes.value);
  const endM = Math.min(dtStrToMinutes(order.end_datetime), dayEndMinutes.value);
  if (endM <= startM) return { display: "none" };
  const left = ((startM - dayStartMinutes.value) / daySpan.value) * 100;
  const width = ((endM - startM) / daySpan.value) * 100;
  return {
    left: `${left}%`,
    width: `${width}%`
  };
};

const onTimelineClick = (event, row) => {
  const container = event.currentTarget;
  const rect = container.getBoundingClientRect();
  if (!rect.width) return;
  const ratio = (event.clientX - rect.left) / rect.width;
  let minutes = dayStartMinutes.value + ratio * daySpan.value;
  // 四舍五入到最近的半小时
  const halfSteps = Math.round(minutes / 30);
  minutes = halfSteps * 30;
  if (minutes < dayStartMinutes.value) minutes = dayStartMinutes.value;
  if (minutes > dayEndMinutes.value - 30) minutes = dayEndMinutes.value - 30;

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
    adjustTimelineRange();
  } catch (err) {
    ElMessage.error("获取日历数据失败");
  }
};

const adjustTimelineRange = () => {
  if (!daySchedules.value.length) {
    timeTicks.value = ["12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00", "22:00", "23:00", "24:00"];
    dayStartMinutes.value = 12 * 60;
    dayEndMinutes.value = 24 * 60;
    if (!form.startTime) {
      form.startTime = "12:00";
    }
    return;
  }
  let minStart = 24 * 60;
  let maxEnd = 0;
  daySchedules.value.forEach((row) => {
    (row.shifts || []).forEach((sh) => {
      const s = timeStrToMinutes(sh.start_time);
      const e = timeStrToMinutes(sh.end_time);
      if (s < minStart) minStart = s;
      if (e > maxEnd) maxEnd = e;
    });
  });
  if (minStart >= maxEnd) {
    minStart = 12 * 60;
    maxEnd = 24 * 60;
  }
  // 向外扩展 1 小时，步进 30 分钟对齐
  minStart = Math.max(0, Math.floor((minStart - 60) / 30) * 30);
  maxEnd = Math.min(24 * 60, Math.ceil((maxEnd + 60) / 30) * 30);
  dayStartMinutes.value = minStart;
  dayEndMinutes.value = maxEnd;
  // 生成时间刻度
  const ticks = [];
  for (let m = minStart; m <= maxEnd; m += 60) {
    const h = Math.floor(m / 60)
      .toString()
      .padStart(2, "0");
    ticks.push(`${h}:00`);
  }
  timeTicks.value = ticks;

  // 若当前选择时间不在范围内，则重置到起始刻度
  const currentM = form.startTime ? timeStrToMinutes(form.startTime) : null;
  if (currentM === null || currentM < minStart || currentM >= maxEnd) {
    form.startTime = minutesToHHMM(minStart);
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
    ElMessage.error("获取当日订单失败");
  }
};

const startDialogVisible = ref(false);
const startForm = reactive({
  id: null,
  start_time: "",
  end_time: ""
});

const openStartDialog = (row) => {
  const pkg = packages.value.find((p) => p.id === row.package_id);
  const duration = pkg?.duration_minutes || 60;
  const now = dayjs();
  const suggestedStart = now.format("HH:mm");
  const suggestedEnd = now.add(duration, "minute").format("HH:mm");
  startForm.id = row.id;
  startForm.start_time = suggestedStart;
  startForm.end_time = suggestedEnd;
  startDialogVisible.value = true;
};

const submitStart = async () => {
  if (!startForm.id || !startForm.start_time || !startForm.end_time) {
    ElMessage.warning("请选择实际开始/结束时间");
    return;
  }
  const start = dayjs(`${selectedDate.value} ${startForm.start_time}:00`);
  const end = dayjs(`${selectedDate.value} ${startForm.end_time}:00`);
  if (!start.isValid() || !end.isValid() || !end.isAfter(start)) {
    ElMessage.warning("结束时间必须晚于开始时间");
    return;
  }
  try {
    await api.put(`/orders/${startForm.id}`, {
      start_datetime: start.format("YYYY-MM-DD HH:mm:ss"),
      end_datetime: end.format("YYYY-MM-DD HH:mm:ss"),
      status: "in_progress"
    });
    ElMessage.success("订单已开始");
    startDialogVisible.value = false;
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

const finishDialogVisible = ref(false);
const finishForm = reactive({
  id: null,
  start_time: "",
  end_time: ""
});

const extendDialogVisible = ref(false);
const extendForm = reactive({
  id: null,
  base_end: "",
  package_id: null,
  preview_end: ""
});
const extendCurrentRow = ref(null);

const openFinishDialog = (row) => {
  finishForm.id = row.id;
  finishForm.start_time = row.start_datetime ? row.start_datetime.split(" ")[1]?.slice(0, 5) : "";
  const now = dayjs();
  finishForm.end_time = now.format("HH:mm");
  finishDialogVisible.value = true;
};

const submitFinish = async () => {
  if (!finishForm.id || !finishForm.end_time) {
    ElMessage.warning("请填写实际结束时间");
    return;
  }
  const startTime = finishForm.start_time || "00:00";
  const start = dayjs(`${selectedDate.value} ${startTime}:00`);
  const end = dayjs(`${selectedDate.value} ${finishForm.end_time}:00`);
  if (!end.isAfter(start)) {
    // 结束时间不晚于开始时间，视为无效服务，释放占用
    try {
      await api.put(`/orders/${finishForm.id}`, { status: "cancelled" });
      ElMessage.success("已释放该预约时间");
      finishDialogVisible.value = false;
      await fetchActiveOrders();
      await fetchDaySchedules();
    } catch (err) {
      ElMessage.error(err?.response?.data?.detail || "释放失败");
    }
    return;
  }
  try {
    await api.put(`/orders/${finishForm.id}`, {
      end_datetime: end.format("YYYY-MM-DD HH:mm:ss"),
      status: "finished"
    });
    ElMessage.success("服务已结束");
    finishDialogVisible.value = false;
    await fetchActiveOrders();
    await fetchDaySchedules();
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || "结束订单失败");
  }
};

const openExtendDialog = (row) => {
  if (!packages.value.length) {
    ElMessage.warning("请先配置套餐后再续钟");
    return;
  }
  const currentEnd = row.end_datetime ? row.end_datetime.split(" ")[1]?.slice(0, 5) : "";
  extendForm.id = row.id;
  extendForm.base_end = currentEnd;
  extendForm.package_id = packages.value[0]?.id || null;
  extendForm.preview_end = currentEnd;
  extendCurrentRow.value = row;
  updateExtendPreview();
  extendDialogVisible.value = true;
};

const updateExtendPreview = () => {
  if (!extendForm.base_end || !extendForm.package_id) {
    extendForm.preview_end = extendForm.base_end;
    return;
  }
  const pkg = packages.value.find((p) => p.id === extendForm.package_id);
  if (!pkg) {
    extendForm.preview_end = extendForm.base_end;
    return;
  }
  const base = dayjs(`${selectedDate.value} ${extendForm.base_end}:00`);
  const newEnd = base.add(pkg.duration_minutes || 0, "minute");
  extendForm.preview_end = newEnd.format("HH:mm");
};

const submitExtend = async () => {
  if (!extendForm.id || !extendForm.base_end || !extendForm.package_id) {
    ElMessage.warning("请选择续钟套餐");
    return;
  }
  const pkg = packages.value.find((p) => p.id === extendForm.package_id);
  if (!pkg) {
    ElMessage.warning("续钟套餐无效");
    return;
  }
  const base = dayjs(`${selectedDate.value} ${extendForm.base_end}:00`);
  const newEnd = base.add(pkg.duration_minutes || 0, "minute");
  const row = extendCurrentRow.value;
  const baseTotal = (row?.total_amount || 0) + (row?.extra_amount || 0);
  const newTotal = baseTotal + (pkg.price || 0);
  const newExtra = (row?.extra_amount || 0) + (pkg.price || 0);
  const noteParts = [];
  if (row?.note) noteParts.push(row.note);
  noteParts.push(`续钟：${pkg.name}（${pkg.duration_minutes}分钟 ¥${pkg.price}）`);
  const newNote = noteParts.join(" | ");
  try {
    await api.put(`/orders/${extendForm.id}`, {
      end_datetime: newEnd.format("YYYY-MM-DD HH:mm:ss"),
      total_amount: newTotal,
      extra_amount: newExtra,
      note: newNote
    });
    ElMessage.success("续钟成功");
    extendDialogVisible.value = false;
    await fetchActiveOrders();
    await fetchDaySchedules();
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || "续钟失败：可能与后续预约冲突");
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
  note: "",
  start_time: "",
  end_time: ""
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
  settleForm.start_time = row.start_datetime
    ? row.start_datetime.split(" ")[1]?.slice(0, 5)
    : "";
  if (row.end_datetime) {
    settleForm.end_time = row.end_datetime.split(" ")[1]?.slice(0, 5);
  } else {
    const pkg = packages.value.find((p) => p.id === row.package_id);
    const duration = pkg?.duration_minutes || 0;
    const start = settleForm.start_time
      ? dayjs(`${selectedDate.value} ${settleForm.start_time}:00`)
      : null;
    if (start && duration > 0) {
      settleForm.end_time = start.add(duration, "minute").format("HH:mm");
    } else {
      settleForm.end_time = "";
    }
  }
  settleDialogVisible.value = true;
};

const settleOrder = async () => {
  if (!settleForm.id) return;
  if (!settleForm.total_amount || !settleForm.payment_method) {
    ElMessage.warning("请填写实收金额和支付方式");
    return;
  }
  const start = settleForm.start_time
    ? dayjs(`${selectedDate.value} ${settleForm.start_time}:00`)
    : null;
  const end = settleForm.end_time
    ? dayjs(`${selectedDate.value} ${settleForm.end_time}:00`)
    : null;
  if (start && end && !end.isAfter(start)) {
    ElMessage.warning("实际结束时间必须晚于实际开始时间");
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
    if (start) payload.start_datetime = start.format("YYYY-MM-DD HH:mm:ss");
    if (end) payload.end_datetime = end.format("YYYY-MM-DD HH:mm:ss");
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

.timeline-wrapper {
  margin-top: 12px;
}

.timeline-scale {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.scale-label {
  width: 60px;
  font-size: 12px;
  color: #666;
}

.scale-bar {
  position: relative;
  flex: 1;
  height: 20px;
  border-bottom: 1px dashed #eee;
}

.scale-tick {
  position: absolute;
  top: 0;
  transform: translateX(-50%);
  font-size: 10px;
  color: #999;
}

.timeline-row {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.staff-col {
  width: 60px;
  font-size: 13px;
  color: #333;
}

.timeline-track {
  position: relative;
  flex: 1;
  height: 32px;
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  overflow: hidden;
  cursor: pointer;
}

.bar {
  position: absolute;
  top: 6px;
  height: 20px;
  border-radius: 4px;
}

.bar.shift {
  background: rgba(82, 196, 26, 0.25);
  z-index: 1;
}

.bar.pending { background: rgba(255, 193, 7, 0.9); z-index: 2; }
.bar.active { background: rgba(255, 112, 67, 0.85); z-index: 3; } /* 柔和橙红 */
.bar.completed { background: rgba(24, 144, 255, 0.9); z-index: 2; }

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

.legend-box.shift { background: rgba(82, 196, 26, 0.25); }
.legend-box.pending { background: rgba(255, 193, 7, 0.9); }
.legend-box.active { background: rgba(255, 112, 67, 0.85); }
.legend-box.completed { background: rgba(24, 144, 255, 0.9); }

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
