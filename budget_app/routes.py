from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from . import db
from .models import Debt, Expense, Income, Source

bp = Blueprint("api", __name__)


@bp.get("/")
def index() -> Any:
    """Return a high level overview of the API endpoints."""
    return jsonify(
        {
            "message": "Kişisel Bütçe API'sine hoş geldiniz",
            "endpoints": {
                "GET /sources": "Harcamalarda kullanılabilecek kaynakları listeler",
                "POST /sources": "Yeni harcama kaynağı oluşturur",
                "GET /expenses": "Harcamaları listeler",
                "POST /expenses": "Yeni harcama kaydı ekler (bölünmüş ya da taksitli olabilir)",
                "GET /debts": "Borçları listeler",
                "POST /debts": "Yeni borç kaydı ekler",
                "GET /incomes": "Gelirleri listeler",
                "POST /incomes": "Yeni gelir kaydı ekler",
            },
        }
    )


@bp.route("/sources", methods=["GET", "POST"])
def sources() -> Any:
    if request.method == "GET":
        all_sources = Source.query.order_by(Source.name).all()
        return jsonify([source.to_dict() for source in all_sources])

    data = request.get_json(silent=True) or {}
    name = data.get("name")
    source_type = data.get("type")
    if not name or not source_type:
        return jsonify({"error": "name ve type alanları gereklidir"}), 400

    if Source.query.filter(Source.name == name).first():
        return jsonify({"error": "Bu isimde bir kaynak zaten mevcut"}), 409

    new_source = Source(name=name, type=source_type)
    db.session.add(new_source)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Bu isimde bir kaynak zaten mevcut"}), 409

    return jsonify(new_source.to_dict()), 201


@bp.route("/sources/<int:source_id>", methods=["GET", "PUT", "DELETE"])
def source_detail(source_id: int) -> Any:
    source = Source.query.get_or_404(source_id)

    if request.method == "GET":
        return jsonify(source.to_dict())

    if request.method == "DELETE":
        db.session.delete(source)
        db.session.commit()
        return "", 204

    data = request.get_json(silent=True) or {}

    new_name = data.get("name")
    if new_name and new_name != source.name:
        duplicate = Source.query.filter(
            Source.name == new_name,
            Source.id != source.id,
        ).first()
        if duplicate:
            return jsonify({"error": "Bu isimde bir kaynak zaten mevcut"}), 409
        source.name = new_name

    if "type" in data:
        source.type = data["type"]

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Bu isimde bir kaynak zaten mevcut"}), 409

    return jsonify(source.to_dict())


@bp.route("/expenses", methods=["GET", "POST"])
def expenses() -> Any:
    if request.method == "GET":
        all_expenses = Expense.query.order_by(Expense.date.desc()).all()
        return jsonify([expense.to_dict() for expense in all_expenses])

    data = request.get_json(silent=True) or {}
    description = data.get("description")
    amount = parse_amount(data.get("amount"))
    date_value = parse_date(data.get("date")) or datetime.utcnow().date()
    category = data.get("category")
    notes = data.get("notes")
    source_id = data.get("source_id")

    if not description or amount is None or source_id is None:
        return (
            jsonify({"error": "description, amount ve source_id alanları gereklidir"}),
            400,
        )

    source = Source.query.get(source_id)
    if source is None:
        return jsonify({"error": "Geçersiz kaynak"}), 400

    expense = Expense(
        description=description,
        amount=amount,
        date=date_value,
        category=category,
        notes=notes,
        source=source,
    )

    split_items = data.get("splits")
    if split_items:
        valid_splits = validate_splits(split_items)
        if valid_splits is None:
            return jsonify({"error": "splits listesi hatalı"}), 400
        expense.splits = valid_splits

    installment = data.get("installment")
    if installment:
        valid_installment = validate_installment(installment)
        if valid_installment is None:
            return jsonify({"error": "installment bilgisi hatalı"}), 400
        expense.installment_count = valid_installment["count"]
        expense.installment_number = valid_installment["number"]
        expense.installment_amount = valid_installment["amount"]

    db.session.add(expense)
    db.session.commit()
    return jsonify(expense.to_dict()), 201


@bp.route("/expenses/<int:expense_id>", methods=["GET", "PUT", "DELETE"])
def expense_detail(expense_id: int) -> Any:
    expense = Expense.query.get_or_404(expense_id)

    if request.method == "GET":
        return jsonify(expense.to_dict())

    if request.method == "DELETE":
        db.session.delete(expense)
        db.session.commit()
        return "", 204

    data = request.get_json(silent=True) or {}

    if "description" in data:
        expense.description = data["description"]
    if "amount" in data:
        amount = parse_amount(data["amount"])
        if amount is None:
            return jsonify({"error": "amount değeri geçersiz"}), 400
        expense.amount = amount
    if "date" in data:
        date_value = parse_date(data["date"])
        if date_value is None:
            return jsonify({"error": "date değeri geçersiz"}), 400
        expense.date = date_value
    if "category" in data:
        expense.category = data["category"]
    if "notes" in data:
        expense.notes = data["notes"]
    if "source_id" in data:
        source = Source.query.get(data["source_id"])
        if source is None:
            return jsonify({"error": "Geçersiz kaynak"}), 400
        expense.source = source
    if "splits" in data:
        splits = data["splits"]
        if splits:
            valid_splits = validate_splits(splits)
            if valid_splits is None:
                return jsonify({"error": "splits listesi hatalı"}), 400
            expense.splits = valid_splits
        else:
            expense.splits = None
    if "installment" in data:
        installment = data["installment"]
        if installment:
            valid_installment = validate_installment(installment)
            if valid_installment is None:
                return jsonify({"error": "installment bilgisi hatalı"}), 400
            expense.installment_count = valid_installment["count"]
            expense.installment_number = valid_installment["number"]
            expense.installment_amount = valid_installment["amount"]
        else:
            expense.installment_count = None
            expense.installment_number = None
            expense.installment_amount = None

    db.session.commit()
    return jsonify(expense.to_dict())


@bp.route("/incomes", methods=["GET", "POST"])
def incomes() -> Any:
    if request.method == "GET":
        all_incomes = Income.query.order_by(Income.received_date.desc()).all()
        return jsonify([income.to_dict() for income in all_incomes])

    data = request.get_json(silent=True) or {}
    source = data.get("source")
    amount = parse_amount(data.get("amount"))
    received_date = parse_date(data.get("received_date")) or datetime.utcnow().date()
    category = data.get("category")
    notes = data.get("notes")

    if not source or amount is None:
        return jsonify({"error": "source ve amount alanları gereklidir"}), 400

    income = Income(
        source=source,
        amount=amount,
        received_date=received_date,
        category=category,
        notes=notes,
    )

    db.session.add(income)
    db.session.commit()
    return jsonify(income.to_dict()), 201


@bp.route("/incomes/<int:income_id>", methods=["GET", "PUT", "DELETE"])
def income_detail(income_id: int) -> Any:
    income = Income.query.get_or_404(income_id)

    if request.method == "GET":
        return jsonify(income.to_dict())

    if request.method == "DELETE":
        db.session.delete(income)
        db.session.commit()
        return "", 204

    data = request.get_json(silent=True) or {}

    if "source" in data:
        income.source = data["source"]
    if "amount" in data:
        amount = parse_amount(data["amount"])
        if amount is None:
            return jsonify({"error": "amount değeri geçersiz"}), 400
        income.amount = amount
    if "received_date" in data:
        received_date = parse_date(data["received_date"])
        if received_date is None:
            return jsonify({"error": "received_date değeri geçersiz"}), 400
        income.received_date = received_date
    if "category" in data:
        income.category = data["category"]
    if "notes" in data:
        income.notes = data["notes"]

    db.session.commit()
    return jsonify(income.to_dict())


@bp.route("/debts", methods=["GET", "POST"])
def debts() -> Any:
    if request.method == "GET":
        all_debts = Debt.query.order_by(Debt.due_date.is_(None), Debt.due_date).all()
        return jsonify([debt.to_dict() for debt in all_debts])

    data = request.get_json(silent=True) or {}
    creditor = data.get("creditor")
    amount = parse_amount(data.get("amount"))
    due_date = parse_date(data.get("due_date"))
    status = data.get("status")
    notes = data.get("notes")

    if not creditor or amount is None:
        return jsonify({"error": "creditor ve amount alanları gereklidir"}), 400

    debt = Debt(
        creditor=creditor,
        amount=amount,
        due_date=due_date,
        status=status,
        notes=notes,
    )

    db.session.add(debt)
    db.session.commit()
    return jsonify(debt.to_dict()), 201


@bp.route("/debts/<int:debt_id>", methods=["GET", "PUT", "DELETE"])
def debt_detail(debt_id: int) -> Any:
    debt = Debt.query.get_or_404(debt_id)

    if request.method == "GET":
        return jsonify(debt.to_dict())

    if request.method == "DELETE":
        db.session.delete(debt)
        db.session.commit()
        return "", 204

    data = request.get_json(silent=True) or {}

    if "creditor" in data:
        debt.creditor = data["creditor"]
    if "amount" in data:
        amount = parse_amount(data["amount"])
        if amount is None:
            return jsonify({"error": "amount değeri geçersiz"}), 400
        debt.amount = amount
    if "due_date" in data:
        due_date = parse_date(data["due_date"])
        if due_date is None:
            return jsonify({"error": "due_date değeri geçersiz"}), 400
        debt.due_date = due_date
    if "status" in data:
        debt.status = data["status"]
    if "notes" in data:
        debt.notes = data["notes"]

    db.session.commit()
    return jsonify(debt.to_dict())


def parse_amount(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value).date()
        except (ValueError, OSError, OverflowError):
            return None
    return None


def validate_splits(splits: Any) -> list[dict[str, Any]] | None:
    if not isinstance(splits, list):
        return None
    cleaned: list[dict[str, Any]] = []
    for item in splits:
        if not isinstance(item, dict):
            return None
        name = item.get("name")
        amount = parse_amount(item.get("amount"))
        if not name or amount is None:
            return None
        cleaned.append({"name": name, "amount": float(amount)})
    return cleaned


def validate_installment(installment: Any) -> dict[str, Any] | None:
    if not isinstance(installment, dict):
        return None
    count = installment.get("count")
    number = installment.get("number")
    amount = parse_amount(installment.get("amount"))

    if count is None or number is None:
        return None
    try:
        count_int = int(count)
        number_int = int(number)
    except (TypeError, ValueError):
        return None
    if count_int <= 0 or number_int <= 0 or number_int > count_int:
        return None

    return {
        "count": count_int,
        "number": number_int,
        "amount": amount if amount is not None else None,
    }
