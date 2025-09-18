from __future__ import annotations

import json
from datetime import date, timedelta
from decimal import Decimal

import click
from flask import current_app
from flask.cli import with_appcontext

from . import db
from .models import Debt, Expense, Income, Source


@click.command("init-db")
@with_appcontext
def init_db_command() -> None:
    """Initialize the SQLite database with demo data."""
    db_path = current_app.config["SQLALCHEMY_DATABASE_URI"]
    click.echo(f"Initializing database at {db_path}")
    db.drop_all()
    db.create_all()

    seed_sources()
    seed_incomes()
    seed_expenses()
    seed_debts()

    db.session.commit()
    click.echo("Database initialized with sample records.")


def seed_sources() -> None:
    sources = [
        Source(name="Kredi Kartı", type="credit_card"),
        Source(name="Nakit", type="cash"),
        Source(name="Borç", type="debt"),
    ]
    db.session.add_all(sources)


def seed_incomes() -> None:
    salary = Income(
        source="Maaş",
        amount=Decimal("35000.00"),
        received_date=date.today().replace(day=1),
        category="Salary",
        notes="Ana gelir kaynağı",
    )
    freelance = Income(
        source="Serbest İş",
        amount=Decimal("5500.00"),
        received_date=date.today() - timedelta(days=10),
        category="Freelance",
        notes="Web sitesi tasarımı projesi",
    )
    db.session.add_all([salary, freelance])


def seed_expenses() -> None:
    card_source = Source.query.filter_by(type="credit_card").first()
    cash_source = Source.query.filter_by(type="cash").first()
    debt_source = Source.query.filter_by(type="debt").first()

    groceries = Expense(
        description="Market alışverişi",
        amount=Decimal("1250.30"),
        date=date.today() - timedelta(days=2),
        category="Food",
        source=card_source,
        split_details=json.dumps([
            {"name": "Gıda", "amount": 900.30},
            {"name": "Temizlik", "amount": 350.00},
        ]),
        notes="Haftalık alışveriş",
    )

    rent_installment = Expense(
        description="Kira taksidi",
        amount=Decimal("7500.00"),
        date=date.today(),
        category="Housing",
        source=debt_source,
        installment_count=12,
        installment_number=5,
        installment_amount=Decimal("7500.00"),
        notes="Ev sahibi ile yapılan taksit anlaşması",
    )

    fuel = Expense(
        description="Benzin",
        amount=Decimal("850.75"),
        date=date.today() - timedelta(days=1),
        category="Transportation",
        source=cash_source,
        notes="Şehir içi kullanım",
    )

    db.session.add_all([groceries, rent_installment, fuel])


def seed_debts() -> None:
    rent_debt = Debt(
        creditor="Ev Sahibi",
        amount=Decimal("90000.00"),
        due_date=date.today() + timedelta(days=240),
        status="active",
        notes="12 taksitli kira borcu",
    )
    credit_card = Debt(
        creditor="Banka X",
        amount=Decimal("5400.00"),
        due_date=date.today() + timedelta(days=20),
        status="active",
        notes="Kredi kartı ekstresi",
    )
    db.session.add_all([rent_debt, credit_card])


def register_cli(app) -> None:
    app.cli.add_command(init_db_command)
