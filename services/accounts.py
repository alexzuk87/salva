"""SALVA Cuenta y SALVA Ahorro — simulación académica."""

from datetime import datetime

import pandas as pd
import streamlit as st

from services.data_store import (
    ACCOUNT_TRANSACTIONS_FILE,
    ACCOUNTS_FILE,
    next_id,
    read_csv,
    write_csv,
)

ACCOUNT_COLUMNS = ["account_id", "user_id", "account_type", "balance", "updated_at"]
TRANSACTION_COLUMNS = [
    "transaction_id", "user_id", "source_account", "destination_account",
    "transaction_type", "amount", "booking_id", "goal_id", "created_at", "status", "description",
]

ACCOUNT_CUENTA = "SALVA_CUENTA"
ACCOUNT_AHORRO = "SALVA_AHORRO"
DEFAULT_USER = "default"

SIM_ALIAS = "salva.alex.demo"
SIM_ACCOUNT_HOLDER = "Alex Demo"
SIM_ACCOUNT_TYPE = "Cuenta virtual SALVA"
SIM_ACCOUNT_ID = "SALVA-DEMO-001"

SIM_DISCLAIMER = (
    "Funcionalidad simulada para fines académicos. "
    "No constituye una cuenta bancaria ni una oferta financiera."
)
FUNDING_EXPLANATION = (
    "Transferí dinero desde otra cuenta para pagar servicios o separar fondos para tus proyectos."
)
ALIAS_DISCLAIMER = (
    "Este alias es ficticio y se utiliza solamente para demostrar el funcionamiento del prototipo."
)


def _next_tx_id(df: pd.DataFrame) -> str:
    if df.empty or "transaction_id" not in df.columns:
        return "TX001"
    nums = df["transaction_id"].str.replace("TX", "", regex=False).astype(int)
    return f"TX{nums.max() + 1:03d}"


def seed_accounts() -> None:
    if ACCOUNTS_FILE.exists():
        df = read_csv(ACCOUNTS_FILE, ACCOUNT_COLUMNS)
        if not df.empty:
            return
    from services.goals import assigned_to_goals

    assigned = assigned_to_goals()
    unassigned_seed = max(85000 - assigned, 25000)
    ahorro_total = assigned + unassigned_seed
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = [
        {"account_id": "ACC001", "user_id": DEFAULT_USER, "account_type": ACCOUNT_CUENTA,
         "balance": "150000", "updated_at": now},
        {"account_id": "ACC002", "user_id": DEFAULT_USER, "account_type": ACCOUNT_AHORRO,
         "balance": str(ahorro_total), "updated_at": now},
    ]
    write_csv(ACCOUNTS_FILE, pd.DataFrame(rows))


def _accounts_df() -> pd.DataFrame:
    seed_accounts()
    return read_csv(ACCOUNTS_FILE, ACCOUNT_COLUMNS)


def ensure_account_integrity() -> None:
    """Garantiza Ahorro total >= asignado a objetivos (corrige datos legacy)."""
    from services.goals import assigned_to_goals as _goal_assigned

    assigned = _goal_assigned()
    df = _accounts_df()
    row = df[df["account_type"] == ACCOUNT_AHORRO]
    if row.empty:
        return
    ahorro = float(row.iloc[0]["balance"] or 0)
    if ahorro < assigned:
        idx = row.index[0]
        df.loc[idx, "balance"] = str(assigned + 25000)
        df.loc[idx, "updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        write_csv(ACCOUNTS_FILE, df)


def load_accounts() -> pd.DataFrame:
    ensure_account_integrity()
    return _accounts_df()


def get_balance(account_type: str) -> float:
    df = load_accounts()
    row = df[df["account_type"] == account_type]
    if row.empty:
        return 0.0
    return float(row.iloc[0]["balance"] or 0)


def assigned_to_goals() -> float:
    from services.goals import assigned_to_goals as _goal_assigned
    return _goal_assigned()


def unassigned_savings() -> float:
    return max(0.0, get_balance(ACCOUNT_AHORRO) - assigned_to_goals())


def _set_balance(account_type: str, new_balance: float) -> None:
    df = _accounts_df()
    idx = df[df["account_type"] == account_type].index
    if idx.empty:
        return
    df.loc[idx, "balance"] = str(max(0, round(new_balance, 2)))
    df.loc[idx, "updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    write_csv(ACCOUNTS_FILE, df)


def load_transactions(limit: int = 20) -> pd.DataFrame:
    df = read_csv(ACCOUNT_TRANSACTIONS_FILE, TRANSACTION_COLUMNS)
    if df.empty:
        return df
    return df.sort_values("created_at", ascending=False).head(limit).reset_index(drop=True)


def _record_tx(
    source: str, dest: str, tx_type: str, amount: float,
    description: str, booking_id: str = "", goal_id: str = "",
) -> dict:
    df = read_csv(ACCOUNT_TRANSACTIONS_FILE, TRANSACTION_COLUMNS)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    row = {
        "transaction_id": _next_tx_id(df),
        "user_id": DEFAULT_USER,
        "source_account": source,
        "destination_account": dest,
        "transaction_type": tx_type,
        "amount": str(amount),
        "booking_id": booking_id,
        "goal_id": goal_id,
        "created_at": now,
        "status": "Completada",
        "description": description,
    }
    write_csv(ACCOUNT_TRANSACTIONS_FILE, pd.concat([df, pd.DataFrame([row])], ignore_index=True))
    return row


def transfer(source: str, dest: str, amount: float, description: str, goal_id: str = "") -> tuple[bool, str, dict | None]:
    if amount <= 0:
        return False, "Ingresá un monto mayor a cero.", None
    key = f"tx_done_{source}_{dest}_{amount}_{goal_id}"
    if st.session_state.get(key):
        return False, "Esta operación ya fue registrada en esta sesión.", None
    if source == ACCOUNT_AHORRO:
        free = unassigned_savings()
        if free < amount:
            return False, "Solo podés transferir el saldo no asignado de SALVA Ahorro.", None
    src_bal = get_balance(source)
    if src_bal < amount:
        return False, "Saldo insuficiente.", None
    _set_balance(source, src_bal - amount)
    _set_balance(dest, get_balance(dest) + amount)
    tx = _record_tx(source, dest, "transferencia", amount, description, goal_id=goal_id)
    st.session_state[key] = True
    return True, "", tx


def deposit_cuenta(amount: float) -> tuple[bool, str, dict | None]:
    if amount <= 0:
        return False, "Ingresá un monto mayor a cero.", None
    key = f"deposit_done_{amount}"
    if st.session_state.get(key):
        return False, "Este ingreso ya fue confirmado en esta sesión.", None
    new_bal = get_balance(ACCOUNT_CUENTA) + amount
    _set_balance(ACCOUNT_CUENTA, new_bal)
    tx = _record_tx("externo", ACCOUNT_CUENTA, "deposito", amount, "Ingreso simulado a SALVA Cuenta")
    st.session_state[key] = True
    st.session_state["last_fund_receipt"] = {
        "amount": amount,
        "balance": new_bal,
        "transaction_id": tx["transaction_id"],
        "created_at": tx["created_at"],
    }
    return True, "", tx


def pay_from_cuenta(amount: float, booking_id: str = "", description: str = "Pago de servicio") -> tuple[bool, str]:
    if amount <= 0:
        return False, "Ingresá un monto válido."
    key = f"pay_svc_{booking_id}_{amount}"
    if st.session_state.get(key):
        return False, "Este pago ya fue registrado."
    bal = get_balance(ACCOUNT_CUENTA)
    if bal < amount:
        return False, "Saldo insuficiente en SALVA Cuenta."
    _set_balance(ACCOUNT_CUENTA, bal - amount)
    _record_tx(ACCOUNT_CUENTA, "servicio", "pago_servicio", amount, description, booking_id=booking_id)
    st.session_state[key] = True
    return True, ""


def account_summary() -> dict:
    cuenta = get_balance(ACCOUNT_CUENTA)
    ahorro = get_balance(ACCOUNT_AHORRO)
    assigned = assigned_to_goals()
    unassigned = max(0.0, ahorro - assigned)
    txs = load_transactions(1)
    last_tx = txs.iloc[0]["description"] if not txs.empty else "Sin movimientos"
    return {
        "cuenta": cuenta,
        "ahorro": ahorro,
        "assigned": assigned,
        "unassigned": unassigned,
        "total": cuenta + ahorro,
        "last_tx": last_tx,
    }


def receipt_html(tx: dict, balance_after: float, title: str = "Operación confirmada") -> str:
    from services.formatting import format_ars
    return (
        f'<div class="receipt-card fade-in">'
        f'<p class="receipt-title">{title}</p>'
        f'<p class="receipt-id">{tx["transaction_id"]}</p>'
        f'<hr class="receipt-divider"/>'
        f'<p><strong>{tx["description"]}</strong></p>'
        f'<p>Monto: {format_ars(float(tx["amount"]))}</p>'
        f'<p>Saldo resultante: {format_ars(balance_after)}</p>'
        f'<p class="body-text">{tx["created_at"]}</p>'
        f'</div>'
    )
