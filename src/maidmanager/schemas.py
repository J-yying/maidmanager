from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class StaffBase(BaseModel):
    name: str = Field(..., description="员工姓名")
    nickname: Optional[str] = Field(None, description="昵称")
    phone: Optional[str] = Field(None, description="联系电话")
    status: Optional[str] = Field("active", description="状态：active/resigned")
    base_salary: Optional[float] = Field(0.0, description="底薪")
    commission_type: Optional[str] = Field(
        "percentage", description="提成类型：percentage/fixed"
    )
    commission_value: Optional[float] = Field(
        0.0, description="提成数值（比例或固定金额）"
    )


class StaffCreate(StaffBase):
    pass


class StaffUpdate(BaseModel):
    """员工更新时的可选字段（部分更新）。"""

    name: Optional[str] = Field(None, description="员工姓名")
    nickname: Optional[str] = Field(None, description="昵称")
    phone: Optional[str] = Field(None, description="联系电话")
    status: Optional[str] = Field(None, description="状态：active/resigned")
    base_salary: Optional[float] = Field(None, description="底薪")
    commission_type: Optional[str] = Field(
        None, description="提成类型：percentage/fixed"
    )
    commission_value: Optional[float] = Field(
        None, description="提成数值（比例或固定金额）"
    )


class StaffRead(StaffBase):
    id: int

    class Config:
        orm_mode = True


class StaffSummary(BaseModel):
    id: int
    name: str
    nickname: Optional[str] = None

    class Config:
        orm_mode = True


class WorkShiftBase(BaseModel):
    staff_id: int = Field(..., description="员工ID")
    date: str = Field(..., description="日期 YYYY-MM-DD")
    start: str = Field(..., description="开始时间 HH:MM 或 HH:MM:ss")
    end: str = Field(..., description="结束时间 HH:MM 或 HH:MM:ss")

    @validator("date")
    def validate_date(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("date 必须是 YYYY-MM-DD 格式") from exc
        return v


class WorkShiftCreate(WorkShiftBase):
    pass


class WorkShiftRead(BaseModel):
    id: int
    staff_id: int
    work_date: str
    start_time: str
    end_time: str
    staff: Optional[StaffSummary] = None

    class Config:
        orm_mode = True


class RosterCopyRequest(BaseModel):
    from_date: str = Field(..., description="源日期 YYYY-MM-DD")
    to_date: str = Field(..., description="目标日期 YYYY-MM-DD")
    override: bool = Field(
        False, description="若目标日期已有排班，是否覆盖（删除后重建）"
    )

    @validator("from_date", "to_date")
    def validate_dates(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("日期必须是 YYYY-MM-DD 格式") from exc
        return v


class OrderCreate(BaseModel):
    staff_id: int = Field(..., description="员工ID")
    customer_name: Optional[str] = Field(None, description="客户名称")
    start_datetime: str = Field(
        ..., description="开始时间，格式 YYYY-MM-DD HH:MM:ss"
    )
    end_datetime: str = Field(
        ..., description="结束时间，格式 YYYY-MM-DD HH:MM:ss"
    )
    total_amount: float = Field(..., description="实收金额")
    package_id: Optional[int] = Field(
        None, description="套餐ID（可选，仅列表中已有的套餐）"
    )
    extra_amount: Optional[float] = Field(
        None, description="额外费用（加项、加时等）"
    )
    payment_method: Optional[str] = Field(
        None, description="支付方式：wechat/alipay/cash"
    )
    note: Optional[str] = Field(None, description="备注")

    @validator("start_datetime", "end_datetime")
    def validate_dt(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
        except ValueError as exc:
            raise ValueError("时间格式必须为 YYYY-MM-DD HH:MM:ss") from exc
        return v


class OrderUpdate(BaseModel):
    """修改订单时允许更新的字段。"""

    customer_name: Optional[str] = Field(None, description="客户名称")
    start_datetime: Optional[str] = Field(
        None, description="开始时间，格式 YYYY-MM-DD HH:MM:ss"
    )
    end_datetime: Optional[str] = Field(
        None, description="结束时间，格式 YYYY-MM-DD HH:MM:ss"
    )
    total_amount: Optional[float] = Field(None, description="实收金额")
    package_id: Optional[int] = Field(
        None, description="套餐ID（可选，仅列表中已有的套餐）"
    )
    extra_amount: Optional[float] = Field(
        None, description="额外费用（加项、加时等）"
    )
    payment_method: Optional[str] = Field(
        None, description="支付方式：wechat/alipay/cash"
    )
    note: Optional[str] = Field(None, description="备注")
    status: Optional[str] = Field(None, description="订单状态：completed/cancelled")

    @validator("start_datetime", "end_datetime")
    def validate_dt_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
        except ValueError as exc:
            raise ValueError("时间格式必须为 YYYY-MM-DD HH:MM:ss") from exc
        return v


class OrderRead(BaseModel):
    id: int
    staff_id: int
    staff_name: Optional[str] = None
    customer_name: Optional[str]
    order_date: str
    start_datetime: str
    end_datetime: str
    duration_minutes: Optional[int]
    total_amount: float
    package_id: Optional[int] = None
    package_name: Optional[str] = None
    extra_amount: Optional[float] = 0.0
    payment_method: Optional[str]
    commission_amount: float
    status: str
    note: Optional[str]
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class AvailableStaffQuery(BaseModel):
    target_time: str = Field(
        ..., description="目标开始时间 YYYY-MM-DD HH:MM:ss"
    )
    duration: int = Field(..., description="时长（分钟）")

    @validator("target_time")
    def validate_target_time(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
        except ValueError as exc:
            raise ValueError("target_time 必须为 YYYY-MM-DD HH:MM:ss") from exc
        return v


class SalaryItem(BaseModel):
    staff_id: int
    staff_name: str
    base_salary: float
    commission_total: float
    total_salary: float


class SalarySlipResponse(BaseModel):
    month: str
    items: List[SalaryItem]


class FinanceDashboardResponse(BaseModel):
    month: str
    total_revenue: float
    total_commission: float
    total_base_salary: float
    total_salary: float
    total_expenses: float
    net_profit: float


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    username: str
    role: str
    token: str


class ExpenseBase(BaseModel):
    title: str = Field(..., description="支出项名称")
    amount: float = Field(..., description="支出金额")
    expense_date: str = Field(..., description="支出日期 YYYY-MM-DD")
    category: Optional[str] = Field(None, description="类别，如 rent/utilities")
    note: Optional[str] = Field(None, description="备注")

    @validator("expense_date")
    def validate_expense_date(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("expense_date 必须是 YYYY-MM-DD 格式") from exc
        return v


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    title: Optional[str] = Field(None, description="支出项名称")
    amount: Optional[float] = Field(None, description="支出金额")
    expense_date: Optional[str] = Field(
        None, description="支出日期 YYYY-MM-DD"
    )
    category: Optional[str] = Field(None, description="类别，如 rent/utilities")
    note: Optional[str] = Field(None, description="备注")

    @validator("expense_date")
    def validate_expense_date(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("expense_date 必须是 YYYY-MM-DD 格式") from exc
        return v


class ExpenseRead(ExpenseBase):
    id: int

    class Config:
        orm_mode = True


class ServicePackageBase(BaseModel):
    name: str = Field(..., description="套餐名称")
    duration_minutes: int = Field(..., description="套餐时长（分钟）")
    price: float = Field(..., description="套餐金额")
    description: Optional[str] = Field(None, description="描述")
    default_commission: Optional[float] = Field(
        0.0, description="默认提成金额（员工配置时的参考）"
    )


class ServicePackageCreate(ServicePackageBase):
    pass


class ServicePackageUpdate(BaseModel):
    name: Optional[str] = Field(None, description="套餐名称")
    duration_minutes: Optional[int] = Field(None, description="套餐时长（分钟）")
    price: Optional[float] = Field(None, description="套餐金额")
    description: Optional[str] = Field(None, description="描述")
    default_commission: Optional[float] = Field(
        None, description="默认提成金额（员工配置时的参考）"
    )


class ServicePackageRead(ServicePackageBase):
    id: int

    class Config:
        orm_mode = True


class StaffDaySchedule(BaseModel):
    staff_id: int
    staff_name: str
    shifts: List[WorkShiftRead]
    pending_orders: List[OrderRead]
    orders: List[OrderRead]


class StaffPackageCommissionItem(BaseModel):
    package_id: int
    package_name: str
    default_commission: float
    staff_commission: Optional[float]


class StaffPackageCommissionUpdateItem(BaseModel):
    package_id: int
    commission_amount: float
