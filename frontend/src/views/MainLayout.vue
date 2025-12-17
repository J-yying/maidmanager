<template>
  <el-container style="height: 100vh">
    <el-aside width="220px" class="sidebar">
      <div class="logo">MaidManager</div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#001529"
        text-color="#fff"
        active-text-color="#ffd04b"
      >
        <el-sub-menu index="basic">
          <template #title>基础配置</template>
          <el-menu-item index="/staff"> 员工管理 </el-menu-item>
          <el-menu-item index="/packages"> 套餐管理 </el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="operation">
          <template #title>运营管理</template>
          <el-menu-item index="/roster"> 排班填报 </el-menu-item>
          <el-menu-item index="/order-calendar"> 工作管理 </el-menu-item>
          <el-menu-item index="/orders"> 历史订单 </el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="finance">
          <template #title>财务管理</template>
          <el-menu-item index="/salary"> 薪资管理 </el-menu-item>
          <el-menu-item index="/expenses"> 其他支出管理 </el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/finance"> 财务报表 </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-left">店铺内部管理系统</div>
        <div class="header-right">
          <span v-if="user">
            当前用户：{{ user.username }}（{{ user.role === "investor" ? "投资人" : "店长" }}）
          </span>
          <el-button type="text" @click="logout">退出登录</el-button>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
  <el-backtop :right="20" :bottom="20" />
</template>

<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();

const activeMenu = computed(() => {
  if (route.path.startsWith("/staff")) return "/staff";
  if (route.path.startsWith("/roster")) return "/roster";
  if (route.path.startsWith("/order-calendar")) return "/order-calendar";
  if (route.path.startsWith("/orders")) return "/orders";
  if (route.path.startsWith("/packages")) return "/packages";
  if (route.path.startsWith("/salary")) return "/salary";
  if (route.path.startsWith("/expenses")) return "/expenses";
  if (route.path.startsWith("/finance")) return "/finance";
  return "/staff";
});

const user = computed(() => {
  const raw = window.localStorage.getItem("mm_user");
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
});

const logout = () => {
  window.localStorage.removeItem("mm_user");
  router.push("/login");
};
</script>

<style scoped>
.sidebar {
  background-color: #001529;
  color: #fff;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  color: #fff;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #f0f0f0;
}

.header-left {
  font-size: 16px;
  font-weight: 500;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
