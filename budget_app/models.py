from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import db


class Source(db.Model):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False)

    expenses: Mapped[list["Expense"]] = relationship("Expense", back_populates="source")

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "type": self.type}


class Expense(db.Model):
    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="expense_amount_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)

    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)
    source: Mapped[Source] = relationship("Source", back_populates="expenses")

    split_details: Mapped[str | None] = mapped_column(Text)
    installment_count: Mapped[int | None] = mapped_column(Integer)
    installment_number: Mapped[int | None] = mapped_column(Integer)
    installment_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "amount": float(self.amount),
            "date": self.date.isoformat(),
            "category": self.category,
            "source": self.source.to_dict() if self.source else None,
            "splits": self.splits,
            "installment": self.installment_info,
            "notes": self.notes,
        }

    @property
    def splits(self) -> list[dict[str, Any]] | None:
        if not self.split_details:
            return None
        try:
            details = json.loads(self.split_details)
        except json.JSONDecodeError:
            return None
        return details

    @splits.setter
    def splits(self, value: list[dict[str, Any]] | None) -> None:
        self.split_details = json.dumps(value) if value else None

    @property
    def installment_info(self) -> dict[str, Any] | None:
        if self.installment_count is None:
            return None
        return {
            "count": self.installment_count,
            "number": self.installment_number,
            "amount": float(self.installment_amount) if self.installment_amount is not None else None,
        }


class Income(db.Model):
    __tablename__ = "incomes"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="income_amount_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    received_date: Mapped[date] = mapped_column(Date, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "amount": float(self.amount),
            "received_date": self.received_date.isoformat(),
            "category": self.category,
            "notes": self.notes,
        }


class Debt(db.Model):
    __tablename__ = "debts"

    id: Mapped[int] = mapped_column(primary_key=True)
    creditor: Mapped[str] = mapped_column(String(120), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str | None] = mapped_column(String(30))
    notes: Mapped[str | None] = mapped_column(Text)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "creditor": self.creditor,
            "amount": float(self.amount),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "status": self.status,
            "notes": self.notes,
        }
