# MaidManager 概要设计（表格版）

## 1. 整体架构与运行环境
- 前端：Vue3 + Vite，静态资源由 Nginx 提供；通过 `/api` 访问后端。
- 后端：FastAPI + SQLite（可迁移至 MySQL/PostgreSQL）；uvicorn 提供服务，Nginx 反代；systemd 管理进程。
- 鉴权与隔离：登录返回伪 token（`Bearer fake-token-<username>`），前端存储；后端所有数据带 `owner` 字段，接口按账号过滤。
- 部署：`scripts/deploy.sh` 自动执行 git pull、依赖安装、前端构建、静态同步、重启后端与 Nginx。

## 2. 数据模型与字段
### 2.1 员工 Staff
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 主键 |
| name | str | 姓名 |
| phone | str | 电话（可空） |
| status | str | 状态：active（在职）/resigned（离职） |
| commission_type | str | 提成类型：percentage（比例）/fixed（固定金额） |
| commission_value | float | 提成数值：比例用小数（0.5 表示 50%），固定为元 |
| owner | str | 账号归属，用于数据隔离 |

### 2.2 套餐 ServicePackage
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 主键 |
| name | str | 套餐名称 |
| duration_minutes | int | 套餐时长（分钟） |
| price | float | 套餐金额（元） |
| default_commission | float | 默认提成（元，固定模式参考） |
| description | str | 描述（可空） |
| owner | str | 数据归属 |

### 2.3 员工套餐提成 StaffPackageCommission
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 主键 |
| staff_id | int | 员工ID |
| package_id | int | 套餐ID |
| commission_amount | float | 提成金额（元） |
| owner | str | 数据归属 |

### 2.4 排班 WorkShift
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 主键 |
| staff_id | int | 员工ID |
| work_date | str | 日期 YYYY-MM-DD |
| start_time | str | 开始时间 HH:MM:ss |
| end_time | str | 结束时间 HH:MM:ss |
| owner | str | 数据归属（唯一约束：owner + work_date + staff_id） |

### 2.5 订单 Order
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 主键 |
| staff_id | int | 员工ID |
| customer_name | str | 客户名称（可空） |
| order_date | str | 下单日期 YYYY-MM-DD |
| start_datetime | str | 开始时间 YYYY-MM-DD HH:MM:ss |
| end_datetime | str | 结束时间 YYYY-MM-DD HH:MM:ss |
| duration_minutes | int | 时长（分钟） |
| booked_minutes | int | 预定总时长（基础套餐 + 续钟累加，分钟） |
| total_amount | float | 实收金额（元，含续钟累加） |
| package_id | int | 套餐ID（可空） |
| package_name | str | 套餐名称快照（可空） |
| extension_package_ids | str | 续钟套餐 ID 列表（JSON 字符串，允许同一套餐多次续钟） |
| extra_amount | float | 额外金额（续钟/加项） |
| payment_method | str | 支付方式：wechat/alipay/cash（可空） |
| commission_amount | float | 提成金额（元） |
| status | str | 状态：pending/in_progress/finished/completed/cancelled |
| note | str | 备注（含续钟记录，可空） |
| owner | str | 数据归属 |

### 2.6 支出 Expense
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 主键 |
| title | str | 支出标题 |
| amount | float | 支出金额（元） |
| expense_date | str | 支出日期 YYYY-MM-DD |
| note | str | 备注（可空） |
| owner | str | 数据归属 |

### 2.7 用户 User（预留）
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 主键 |
| username | str | 用户名 |
| password_hash | str | 密码哈希 |
| role | str | 角色（manager/investor 等） |

## 3. 接口设计（主要接口，入参/出参表格）
> 说明：所有接口需带 `Authorization: Bearer fake-token-<username>`；返回统一包含 HTTP 状态码和 JSON 数据（此处列主要字段）。

### 3.1 登录
- `POST /api/login`
  - 入参：
    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | username | str | 用户名 |
    | password | str | 密码 |
  - 出参：
    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | username | str | 用户名 |
    | role | str | 角色 |
    | token | str | 伪 token，需放入 Authorization |

### 3.2 员工
- `GET /api/staff`
  - 入参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | status | str | 在职/离职（可选） |

  - 出参：员工列表（同 Staff 字段）
- `POST /api/staff` / `PUT /api/staff/{id}`
  - 入参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | name | str | 姓名 |
    | phone | str | 电话（可空） |
    | status | str | 在职/离职 |
    | commission_type | str | 提成类型：比例/固定金额 |
    | commission_value | float | 提成数值：比例用小数，固定用元 |

  - 出参：员工对象
- `GET /api/staff/{id}/package_commissions`
  - 出参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | package_id | int | 套餐ID |
    | package_name | str | 套餐名称 |
    | default_commission | float | 套餐默认提成 |
    | staff_commission | float | 员工定制提成（可空） |

- `PUT /api/staff/{id}/package_commissions`
  - 入参：列表，每项 {package_id, commission_amount}；无返回体

### 3.3 套餐
- `GET /api/packages`：出参套餐列表
- `POST /api/packages` / `PUT /api/packages/{id}` / `DELETE /api/packages/{id}`
  - 入参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | name | str | 套餐名称 |
    | duration_minutes | int | 套餐时长（分钟） |
    | price | float | 套餐金额（元） |
    | default_commission | float | 默认提成（元，可空） |
    | description | str | 描述（可空） |

  - 出参：套餐对象（删除无返回体）

### 3.4 排班
- `GET /api/roster`
  - 入参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | date | str | YYYY-MM-DD |

  - 出参：排班列表（字段同下）
- `POST /api/roster`
  - 入参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | staff_id | int | 员工ID |
    | date | str | 日期 YYYY-MM-DD |
    | start | str | 开始时间 HH:MM 或 HH:MM:ss |
    | end | str | 结束时间 HH:MM 或 HH:MM:ss |

  - 出参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | id | int | 排班ID |
    | staff_id | int | 员工ID |
    | work_date | str | 日期 |
    | start_time | str | 开始时间 |
    | end_time | str | 结束时间 |
    | owner | str | 数据归属 |
- `PUT /api/roster/{id}`
  - 入参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | start | str | 开始时间 |
    | end | str | 结束时间 |

  - 出参：同上排班字段
- `POST /api/roster/copy`
  - 入参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | from_date | str | 源日期 YYYY-MM-DD |
    | to_date | str | 目标日期 YYYY-MM-DD |
    | override | bool | 是否覆盖目标日已有排班 |

  - 出参：目标日期排班列表（同排班字段）
- `DELETE /api/roster/{id}`
  - 入参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | id | int | 排班ID（路径参数） |

  - 出参：无（204），若当日存在未取消订单则报错
- `GET /api/roster/marks`
  - 入参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | month | str | 月份 YYYY-MM |

  - 出参：有排班的日期列表（字符串数组，如 `["2025-12-16", ...]`）

### 3.5 订单/预约
- `GET /api/orders/day_view`
  - 入参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | date | str | 日期 YYYY-MM-DD |

  - 出参：员工维度的排班 + 订单（包含 pending/in_progress/finished/completed）

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | staff_id | int | 员工ID |
    | staff_name | str | 员工姓名 |
    | shifts | list | 排班列表（id, work_date, start_time, end_time） |
    | pending_orders | list | 待开始订单 |
    | orders | list | 进行中/待结算/已完成订单 |
- `GET /api/orders/active`
  - 入参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | date | str | 日期 YYYY-MM-DD |

  - 出参：当日待开始/进行中/待结算/已完成订单列表

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | id | int | 订单ID |
    | staff_id | int | 员工ID |
    | staff_name | str | 员工姓名 |
    | customer_name | str | 客户名（可空） |
    | start_datetime | str | 开始时间 |
    | end_datetime | str | 结束时间 |
    | package_name | str | 套餐名 |
    | status | str | 状态 |
    | total_amount | float | 实收金额 |
    | note | str | 备注（可空） |
- `GET /api/orders/marks`
  - 入参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | month | str | 月份 YYYY-MM |

  - 出参：存在进行中/待结算/已完成订单的日期列表（字符串数组）
- `GET /api/available_staff`
  - 入参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | target_time | str | 开始时间 YYYY-MM-DD HH:MM:ss |
    | duration | int | 时长（分钟） |
  - 出参：可用员工列表

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | id | int | 员工ID |
    | name | str | 姓名 |
    | status | str | 在职/离职 |
    | commission_type | str | 提成类型 |
    | commission_value | float | 提成数值 |
- `POST /api/orders`
  - 入参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | staff_id | int | 员工ID |
    | start_datetime | str | 开始时间 YYYY-MM-DD HH:MM:ss |
    | end_datetime | str | 结束时间 YYYY-MM-DD HH:MM:ss |
    | total_amount | float | 实收金额（元） |
    | package_id | int | 套餐ID（可空） |
    | extra_amount | float | 额外金额（可空） |
    | payment_method | str | 支付方式（可空） |
    | note | str | 备注（可空） |

  - 出参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | id | int | 订单ID |
    | staff_id | int | 员工ID |
    | staff_name | str | 员工姓名 |
    | start_datetime | str | 开始时间 |
    | end_datetime | str | 结束时间 |
    | total_amount | float | 实收金额 |
    | package_id | int | 套餐ID（可空） |
    | package_name | str | 套餐名称 |
    | extra_amount | float | 额外金额 |
    | payment_method | str | 支付方式 |
    | commission_amount | float | 提成金额 |
    | status | str | 状态 |
    | note | str | 备注 |
    | created_at | str | 创建时间 |
- `PUT /api/orders/{id}`
  - 入参：可选字段（start/end、total_amount、extra_amount、payment_method、note、status 等）
  - 出参：订单对象（同上字段）
- `GET /api/orders`
  - 入参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | from_date | str | 起始日期 YYYY-MM-DD（可空） |
    | to_date | str | 结束日期 YYYY-MM-DD（可空） |

  - 出参：历史订单列表（同订单字段）

### 3.6 支出
- `GET /api/expenses`
  - 入参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | month | str | 月份 YYYY-MM（可空） |

  - 出参：支出列表（Expense 字段）
- `POST /api/expenses`
  - 入参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | title | str | 标题 |
    | amount | float | 金额（元） |
    | expense_date | str | 日期 YYYY-MM-DD |
    | note | str | 备注（可空） |

  - 出参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | id | int | 支出ID |
    | title | str | 标题 |
    | amount | float | 金额（元） |
    | expense_date | str | 日期 |
    | note | str | 备注 |
    | owner | str | 数据归属 |
- `PUT /api/expenses/{id}` / `DELETE /api/expenses/{id}`：同上入参（路径 id），出参支出对象/无

### 3.7 财务
- `GET /api/finance/salary_slip`
  - 入参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | month | str | 月份 YYYY-MM |

  - 出参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | month | str | 月份 |
    | items | list | 工资条列表 |
    | items[].staff_id | int | 员工ID |
    | items[].staff_name | str | 员工姓名 |
    | items[].base_salary | float | 底薪 |
    | items[].commission_total | float | 提成总额 |
    | items[].total_salary | float | 应发合计 |
- `GET /api/finance/dashboard`
  - 入参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | month | str | 月份 YYYY-MM |

  - 出参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | month | str | 月份 |
    | total_revenue | float | 总营收 |
    | total_commission | float | 总提成 |
    | total_base_salary | float | 总底薪 |
    | total_salary | float | 总薪资 |
    | total_expenses | float | 总支出 |
    | net_profit | float | 净利润 |
- `GET /api/finance/attendance`
  - 入参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | month | str | 月份 YYYY-MM |

  - 出参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | month | str | 月份 |
    | items | list | 按员工出勤汇总 |
    | items[].staff_id | int | 员工ID |
    | items[].staff_name | str | 员工姓名 |
    | items[].shift_days | int | 排班天数 |
    | items[].shift_hours | float | 排班时长（小时） |
    | items[].completed_order_count | int | 已完成订单数 |
    | items[].completed_order_hours | float | 已完成订单总时长（小时，基于 booked_minutes） |
- `GET /api/finance/roster_overview`
  - 入参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | month | str | 月份 YYYY-MM |

  - 出参：

    | 字段 | 类型 | 说明 |
    | --- | --- | --- |
    | month | str | 月份 |
    | total_shift_hours | float | 总排班时长（小时） |
    | total_package_hours | float | 套餐总钟数（小时，基于 booked_minutes） |
    | shift_days | int | 排班天数 |
    | avg_daily_shift_hours | float | 日均排班时长（小时） |
    | earliest_start | str | 最早开始时间（HH:MM:ss，可空） |
    | latest_end | str | 最晚结束时间（HH:MM:ss，可空） |

## 4. 前后端交互与流程
- 登录后前端保存 token，axios header 自动带 Authorization。
- 排班创建/编辑后，通过 `/api/orders/day_view` 展示在班色块与订单覆盖。
- 预约创建：先 `/api/available_staff` 过滤重叠，再 `POST /api/orders` 创建。
- 开始/续钟/结束/结算：使用 `PUT /api/orders/{id}` 分阶段更新时间、金额、状态；续钟冲突由后端校验。
- 当日订单视图：`/api/orders/active` 提供待开始/进行中/待结算/已完成（当日）；已完成只读。
- 支出：录入与列表分栏，删除前端确认后调用 `DELETE`。
- 财务：按月调用工资条与总览。

## 5. 业务场景与规则（顺序）
1) 套餐 → 员工 → 排班 → 预约 → 开始/续钟 → 结束 → 结算
2) 支出：按日录入、按月查看/编辑/删除
3) 财务：按月查看工资条与财务总览
4) 规则与校验：
   - 排班唯一：owner+日期+员工唯一；启动时去重。
   - 时间重叠校验：预约/续钟不得与非取消订单重叠（分钟级）。
   - 状态流转：pending → in_progress → finished → completed；任意阶段可取消。
   - 结束校验：结束≤开始则自动取消释放占用。
   - 续钟：延长结束、累加金额/备注，冲突则失败。
   - 提成：比例小数存储，UI 百分比输入；固定金额可按套餐单独配置。

## 6. 前端要点
- 时间轴动态刻度（排班最早/最晚），色块分层：在班/待开始/进行中/已完成。
- 时间选择支持任意分钟，自动刷新可用员工；进行中可续钟，结束校验时间。
- 支出录入与列表分栏，删除需确认，表单可重置；提成输入带“%”附加栏。
- 财务：出勤/排班概览按小时聚合；套餐钟数基于 `booked_minutes`。
- 日历标记：提供 `/api/roster/marks` 与 `/api/orders/marks` 返回当月有排班/订单的日期，前端在排班、工作管理日历上显示标记（当前标记渲染存在问题，见 TODO）。

## 7. 部署与运维
- Nginx 80 反代 uvicorn 8000，静态前端由 Nginx 提供。
- `scripts/deploy.sh`：git pull → 虚拟环境依赖 → 前端构建 → 同步静态 → 重启后端、重载 Nginx。
- 日志：systemd（后端）、Nginx；默认 SQLite 存储（可迁移其他 DB）。

## 8. TODO
- Element Plus 日期选择器未正确展示排班/订单绿点标记，需排查自定义单元格插槽与样式覆盖，确保 `/api/roster/marks`、`/api/orders/marks` 返回的日期能落盘显示。
