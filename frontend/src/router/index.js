import { createRouter, createWebHistory } from "vue-router";
import LoginView from "../views/LoginView.vue";
import StaffListView from "../views/StaffListView.vue";
import RosterView from "../views/RosterView.vue";
import OrderView from "../views/OrderView.vue";
import OrderListView from "../views/OrderListView.vue";
import PackageListView from "../views/PackageListView.vue";
import SalaryView from "../views/SalaryView.vue";
import ExpenseManagementView from "../views/ExpenseManagementView.vue";
import FinanceDashboardView from "../views/FinanceDashboardView.vue";
import MainLayout from "../views/MainLayout.vue";

const routes = [
  {
    path: "/login",
    name: "login",
    component: LoginView
  },
  {
    path: "/",
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: "",
        redirect: "/staff"
      },
      {
        path: "staff",
        name: "staff",
        component: StaffListView
      },
      {
        path: "roster",
        name: "roster",
        component: RosterView
      },
      {
        path: "order-calendar",
        name: "orderCalendar",
        component: OrderView
      },
      {
        path: "orders",
        name: "orders",
        component: OrderListView
      },
      {
        path: "packages",
        name: "packages",
        component: PackageListView
      },
      {
        path: "salary",
        name: "salary",
        component: SalaryView
      },
      {
        path: "expenses",
        name: "expenses",
        component: ExpenseManagementView
      },
      {
        path: "finance",
        name: "finance",
        component: FinanceDashboardView
      }
    ]
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to, from, next) => {
  if (to.path === "/login") {
    next();
    return;
  }

  const raw = window.localStorage.getItem("mm_user");
  if (to.meta.requiresAuth && !raw) {
    next({ path: "/login" });
    return;
  }

  next();
});

export default router;
