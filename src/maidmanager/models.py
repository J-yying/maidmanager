from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    """系统用户（店长 / 投资人）。

    当前 MVP 暂不做真实鉴权，仅保留表结构以便后续扩展。
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="manager")  # manager / investor


class Staff(Base):
    """员工档案与薪资配置。"""

    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    nickname = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    status = Column(String, default="active")  # active / resigned
    owner = Column(String, nullable=False, index=True, default="manager")

    base_salary = Column(Float, default=0.0)
    commission_type = Column(
        String, default="percentage"
    )  # percentage / fixed
    commission_value = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)

    work_shifts = relationship("WorkShift", back_populates="staff")
    orders = relationship("Order", back_populates="staff")


class WorkShift(Base):
    """排班时段（解决碎片化排班）。"""

    __tablename__ = "work_shifts"

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False)
    work_date = Column(String, nullable=False)  # YYYY-MM-DD
    start_time = Column(String, nullable=False)  # HH:MM:ss
    end_time = Column(String, nullable=False)  # HH:MM:ss
    created_at = Column(DateTime, default=datetime.utcnow)
    owner = Column(String, nullable=False, index=True, default="manager")

    staff = relationship("Staff", back_populates="work_shifts")


class Order(Base):
    """订单记录，包含提成快照。"""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False)
    customer_name = Column(String, nullable=True)

    order_date = Column(String, nullable=False)  # YYYY-MM-DD
    start_datetime = Column(String, nullable=False)  # YYYY-MM-DD HH:MM:ss
    end_datetime = Column(String, nullable=False)  # YYYY-MM-DD HH:MM:ss
    duration_minutes = Column(Integer, nullable=True)
    booked_minutes = Column(Integer, nullable=True, default=0)
    extension_package_ids = Column(String, nullable=True)  # JSON 数组，续钟套餐ID列表

    total_amount = Column(Float, nullable=False)
    payment_method = Column(String, nullable=True)  # wechat / alipay / cash

    package_id = Column(Integer, ForeignKey("service_packages.id"), nullable=True)
    package_name = Column(String, nullable=True)  # 快照：下单时的套餐名
    extra_amount = Column(Float, default=0.0)

    commission_amount = Column(Float, default=0.0)

    status = Column(String, default="pending")  # pending / in_progress / finished / completed / cancelled
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner = Column(String, nullable=False, index=True, default="manager")

    staff = relationship("Staff", back_populates="orders")
    package = relationship("ServicePackage", uselist=False)


class Expense(Base):
    """其他支出记录（房租、水电等）。"""

    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    expense_date = Column(String, nullable=False)  # YYYY-MM-DD
    category = Column(String, nullable=True)  # rent / utilities / supplies
    note = Column(Text, nullable=True)
    owner = Column(String, nullable=False, index=True, default="manager")


class ServicePackage(Base):
    """服务套餐定义（时长 + 金额）。"""

    __tablename__ = "service_packages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # 套餐名称，如「标准 60 分钟」
    duration_minutes = Column(Integer, nullable=False)  # 套餐时长（分钟）
    price = Column(Float, nullable=False)  # 套餐金额
    description = Column(Text, nullable=True)
    default_commission = Column(Float, default=0.0)  # 默认提成金额（作为员工配置的参考）
    owner = Column(String, nullable=False, index=True, default="manager")


class StaffPackageCommission(Base):
    """员工针对每个套餐的固定提成配置。"""

    __tablename__ = "staff_package_commissions"

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False)
    package_id = Column(Integer, ForeignKey("service_packages.id"), nullable=False)
    commission_amount = Column(Float, nullable=False, default=0.0)
    owner = Column(String, nullable=False, index=True, default="manager")
