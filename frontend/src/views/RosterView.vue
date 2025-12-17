<template>
  <div>
    <div class="toolbar">
      <div class="left">
        <el-date-picker
          v-model="selectedDate"
          type="date"
          placeholder="选择日期"
          value-format="YYYY-MM-DD"
          @change="fetchRoster"
        />
        <el-button type="primary" @click="fetchRoster">刷新排班</el-button>
      </div>
      <div class="right">
        <el-button v-if="selectedDate && selectedDate !== todayStr" @click="copyToToday">
          将该日排班复制到今天
        </el-button>
        <el-button type="primary" @click="openCreate">新增排班</el-button>
      </div>
    </div>

    <el-table :data="shifts" border style="width: 100%">
      <el-table-column type="index" label="序号" width="60" />
      <el-table-column label="员工">
        <template #default="{ row }">
          {{ row.staff?.name || row.staff_id }}
        </template>
      </el-table-column>
      <el-table-column prop="work_date" label="日期" width="120" />
      <el-table-column prop="start_time" label="开始时间" width="120" />
      <el-table-column prop="end_time" label="结束时间" width="120" />
      <el-table-column label="操作" width="200" align="center">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="confirmDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="480px">
      <el-form :model="form" label-width="96px">
        <el-form-item label="员工">
          <el-select v-model="form.staff_id" placeholder="选择员工" :disabled="!!editingId">
            <el-option v-for="s in staffOptions" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker
            v-model="form.date"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            :disabled="!!editingId"
          />
        </el-form-item>
        <el-form-item label="开始时间">
          <el-time-select
            v-model="form.start"
            start="08:00"
            step="00:30"
            end="24:00"
            placeholder="选择开始时间（整点或半点）"
          />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-time-select
            v-model="form.end"
            start="08:00"
            step="00:30"
            end="24:00"
            placeholder="选择结束时间（整点或半点）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import dayjs from "dayjs";
import api from "../api/client";

const selectedDate = ref(dayjs().format("YYYY-MM-DD"));
const todayStr = dayjs().format("YYYY-MM-DD");
const shifts = ref([]);
const dialogVisible = ref(false);
const submitting = ref(false);
const editingId = ref(null);
const staffOptions = ref([]);

const form = reactive({
  staff_id: null,
  date: dayjs().format("YYYY-MM-DD"),
  start: "14:00",
  end: "22:00"
});

const dialogTitle = computed(() => (editingId.value ? "编辑排班" : "新增排班"));

const formatTime = (t) => {
  if (!t) return t;
  // 支持 HH:MM 或 HH:MM:SS，统一裁剪为 HH:MM
  return t.slice(0, 5);
};

const fetchRoster = async () => {
  if (!selectedDate.value) return;
  try {
    const { data } = await api.get("/roster", {
      params: { date: selectedDate.value }
    });
    shifts.value = data.map((item) => ({
      ...item,
      start_time: formatTime(item.start_time),
      end_time: formatTime(item.end_time)
    }));
  } catch (err) {
    ElMessage.error("获取排班失败");
  }
};

const fetchStaffOptions = async () => {
  try {
    const { data } = await api.get("/staff", { params: { status: "active" } });
    staffOptions.value = data;
  } catch (err) {
    ElMessage.error("获取员工列表失败");
  }
};

const openCreate = () => {
  form.staff_id = staffOptions.value[0]?.id || null;
  form.date = selectedDate.value || dayjs().format("YYYY-MM-DD");
  form.start = "14:00";
  form.end = "22:00";
  editingId.value = null;
  dialogVisible.value = true;
};

const copyToToday = async () => {
  if (!selectedDate.value || selectedDate.value === todayStr) return;
  try {
    const { data: todayRoster } = await api.get("/roster", {
      params: { date: todayStr }
    });

    let override = false;
    if (todayRoster.length > 0) {
      await ElMessageBox.confirm(
        "今天已有排班，是否覆盖为当前日期的排班？",
        "提示",
        {
          type: "warning",
          confirmButtonText: "覆盖",
          cancelButtonText: "取消"
        }
      );
      override = true;
    }

    await api.post("/roster/copy", {
      from_date: selectedDate.value,
      to_date: todayStr,
      override
    });
    ElMessage.success("复制排班到今天成功");
    selectedDate.value = todayStr;
    fetchRoster();
  } catch (err) {
    if (err === "cancel" || err?.message?.includes("cancel")) {
      return;
    }
    ElMessage.error(err?.response?.data?.detail || "复制排班失败");
  }
};

const openEdit = (row) => {
  editingId.value = row.id;
  form.staff_id = row.staff_id;
  form.date = row.work_date;
  form.start = formatTime(row.start_time);
  form.end = formatTime(row.end_time);
  dialogVisible.value = true;
};

const confirmDelete = (row) => {
  ElMessageBox.confirm(
    "删除前请确保当日该员工的预约/订单已取消。确定删除该排班？",
    "删除确认",
    {
      type: "warning",
      confirmButtonText: "删除",
      cancelButtonText: "取消"
    }
  )
    .then(async () => {
      try {
        await api.delete(`/roster/${row.id}`);
        ElMessage.success("删除排班成功");
        fetchRoster();
      } catch (err) {
        ElMessage.error(err?.response?.data?.detail || "删除排班失败");
      }
    })
    .catch(() => {});
};

const submitForm = async () => {
  if (!form.staff_id || !form.date) {
    ElMessage.warning("请填写完整排班信息");
    return;
  }
  submitting.value = true;
  try {
    if (editingId.value) {
      await api.put(`/roster/${editingId.value}`, {
        start: form.start,
        end: form.end
      });
      ElMessage.success("更新排班成功");
    } else {
      await api.post("/roster", form);
      ElMessage.success("新增排班成功");
    }
    dialogVisible.value = false;
    selectedDate.value = form.date;
    fetchRoster();
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || "操作失败");
  } finally {
    submitting.value = false;
  }
};

onMounted(() => {
  fetchStaffOptions();
  fetchRoster();
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
</style>
