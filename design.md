
-----

### 一、 技术架构选型 (Tech Stack)

为了让你能最快在本地电脑（Windows/Mac）上把系统跑起来：

  * **后端框架：** **Python FastAPI**
      * *理由：* 现代化、速度快、代码极简。自带 Swagger UI 文档（写完接口打开浏览器就能测，非常适合不需要专门前端配合的独立开发）。
  * **数据库：** **SQLite**
      * *理由：* 无需安装任何软件，就是一个文件（`maid_system.db`）。Python 原生支持，以后要迁移到 MySQL/PostgreSQL 改一行配置就行。
  * **前端框架：** **Vue 3 + Element Plus (PC端) / Vant UI (移动端)**
      * *理由：* 这是一个管理后台，Element Plus 提供了现成的表格、日历、表单组件。如果是简单的 Mobile Web，可以通过 CSS 适配，或者混用组件库。
  * **运行环境：** 本地 `localhost`。

-----

### 二、 数据库详细设计 (Schema)

这是一个基于 **SQLite** 的 SQL 设计（直接复制可以运行）。我针对“排班”和“订单快照”做了特别优化。

```sql
-- 1. 管理员/投资人表 (最简单的鉴权)
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'manager' -- 'manager'(店长) 或 'investor'(投资人)
);

-- 2. 员工表 (女仆档案 & 薪资配置)
CREATE TABLE staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    nickname TEXT,              -- 昵称，如 "小爱"
    phone TEXT,
    status TEXT DEFAULT 'active', -- active(在职), resigned(离职)
    
    -- 薪资配置 (简化版，直接挂在人身上)
    base_salary REAL DEFAULT 0,      -- 底薪，如 3000.00
    commission_type TEXT DEFAULT 'percentage', -- 'percentage'(比例) 或 'fixed'(固定额)
    commission_value REAL DEFAULT 0, -- 如 0.4 (40%) 或 200 (每单200元)
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 3. 排班时段表 (核心：解决了碎片化排班问题)
CREATE TABLE work_shifts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    staff_id INTEGER NOT NULL,
    work_date TEXT NOT NULL,      -- 格式 'YYYY-MM-DD'
    start_time TEXT NOT NULL,     -- 格式 'HH:MM:ss' (如 '14:00:00')
    end_time TEXT NOT NULL,       -- 格式 'HH:MM:ss' (如 '22:00:00')
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (staff_id) REFERENCES staff(id)
);

-- 4. 订单表 (核心：记录收支与提成快照)
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    staff_id INTEGER NOT NULL,
    customer_name TEXT,           -- 客户标识，如 "王总"
    
    -- 时间记录
    order_date TEXT NOT NULL,     -- 'YYYY-MM-DD'
    start_datetime TEXT NOT NULL, -- 'YYYY-MM-DD HH:MM:ss'
    end_datetime TEXT NOT NULL,   -- 'YYYY-MM-DD HH:MM:ss'
    duration_minutes INTEGER,     -- 时长，方便统计
    
    -- 财务记录
    total_amount REAL NOT NULL,   -- 实收金额 (营收)
    payment_method TEXT,          -- 'wechat', 'alipay', 'cash'
    
    -- 薪资快照 (重点：下单那一刻算出来的提成，后续改规则不影响旧单)
    commission_amount REAL DEFAULT 0, 
    
    status TEXT DEFAULT 'completed', -- 'completed', 'cancelled'
    note TEXT,                    -- 备注
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (staff_id) REFERENCES staff(id)
);

-- 5. 其他支出表 (投资人记房租水电)
CREATE TABLE expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,          -- 支出项：房租、水电
    amount REAL NOT NULL,
    expense_date TEXT NOT NULL,
    category TEXT,                -- 'rent', 'utilities', 'supplies'
    note TEXT
);
```

-----

### 三、 后端接口设计 (API Specs)

这里列出核心业务接口，**你可以直接照着这个逻辑去写 Python 代码**。

#### 模块 A：人员与配置 (Staff)

1.  **`POST /api/staff` (新增员工)**

      * **输入:** `{ "name": "娜娜", "base_salary": 3000, "commission_value": 0.4 }`
      * **逻辑:** 简单的 Insert。

2.  **`GET /api/staff` (员工列表)**

      * **输出:** 返回所有员工信息。

#### 模块 B：排班管理 (Roster)

3.  **`GET /api/roster?date=2025-11-19` (获取某日排班)**

      * **逻辑:** 查询 `work_shifts` 表，返回当天所有上班的女仆及其时段。
      * **前端展示:** 根据返回的时间段，渲染甘特图/时间条。

4.  **`POST /api/roster` (新增/修改排班)**

      * **输入:** `{ "staff_id": 1, "date": "2025-11-19", "start": "14:00", "end": "22:00" }`
      * **逻辑:** 插入数据。*进阶逻辑：检查该时间段是否已经存在，避免重复录入。*

#### 模块 C：业务开单 (Order) —— **逻辑最复杂**

5.  **`GET /api/available_staff` (查询当前空闲女仆)**

      * **场景:** 店长开单时，下拉框里只显示能接单的人。
      * **输入:** `{ "target_time": "2025-11-19 15:00:00", "duration": 60 }` (查下午3点做1小时谁有空)
      * **逻辑 (后端核心算法):**
        1.  `Select * from work_shifts` where 时间覆盖了 15:00-16:00。
        2.  `Select * from orders` where 此人已经在 15:00-16:00 有单子了。
        3.  **集合做减法**：(排班的人) - (正在忙的人) = **可用列表**。

6.  **`POST /api/orders` (创建订单/结账)**

      * **输入:** `{ "staff_id": 1, "customer": "王总", "amount": 600, "start": "...", "end": "..." }`
      * **逻辑:**
        1.  读取 `staff` 表，获取该员工当前的 `commission_value` (比如 0.4)。
        2.  计算提成：`600 * 0.4 = 240`。
        3.  将 `240` 写入 `orders.commission_amount` 字段 (快照)。
        4.  保存订单。

#### 模块 D：财务报表 (Finance)

7.  **`GET /api/finance/salary_slip?month=2025-11` (工资条)**

      * **逻辑:**
          * `底薪` = 查询 staff.base\_salary
          * `提成总额` = Sum(orders.commission\_amount) where month='2025-11' and staff\_id=X
          * `应发工资` = 底薪 + 提成总额

8.  **`GET /api/finance/dashboard?month=2025-11` (老板看板)**

      * **逻辑:**
          * `总营收` = Sum(orders.total\_amount)
          * `总工资支出` = Sum(所有人的应发工资)
          * `其他支出` = Sum(expenses.amount)
          * `净利润` = 总营收 - 总工资支出 - 其他支出

-----