<template>
  <div class="login-page">
    <el-card class="login-card">
      <h2 class="title">MaidManager 登录</h2>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" autocomplete="off" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" autocomplete="off" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="onSubmit">
            登录
          </el-button>
        </el-form-item>
        <el-alert
          title="测试账号：manager / investor，密码分别为 manager123 / investor123"
          type="info"
          show-icon
        />
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import api from "../api/client";

const router = useRouter();
const formRef = ref();

const form = reactive({
  username: "manager",
  password: "manager123"
});

const rules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }]
};

const submitting = ref(false);

const onSubmit = () => {
  if (!formRef.value) return;
  formRef.value.validate(async (valid) => {
    if (!valid) return;
    submitting.value = true;
    try {
      const { data } = await api.post("/login", form);
      window.localStorage.setItem("mm_user", JSON.stringify(data));
      ElMessage.success("登录成功");
      router.push("/staff");
    } catch (err) {
      ElMessage.error(err?.response?.data?.detail || "登录失败");
    } finally {
      submitting.value = false;
    }
  });
};
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
}

.login-card {
  width: 380px;
}

.title {
  text-align: center;
  margin-bottom: 16px;
}
</style>

