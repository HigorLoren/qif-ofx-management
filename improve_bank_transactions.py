from datetime import datetime
import re
from utils import fix_time
from ofxtools.models import STMTTRN
from ofxtools.models.wrapperbases import TranList

BANK_NAMES = {33: "Santander", 77: "Inter"}


def improve_inter_transaction(transaction: STMTTRN):
    if "/" in transaction.fitid:
        transaction.fitid = "000000"

    if transaction.checknum == "077":
        transaction.checknum = "000"

    if transaction.refnum == "077":
        transaction.refnum = "000"

    _pix_memo_match = re.match(
        r"(?P<memo>PIX (RECEBIDO|ENVIADO) - Cp *: *[\d-]+)-(?P<actor>[\w ]+)",
        transaction.memo,
    )

    if _pix_memo_match:
        transaction.memo = _pix_memo_match.group("memo")
        transaction.name = _pix_memo_match.group("actor")
    else:
        _pix_interno_match = re.match(
            r"(?P<memo>PIX ENVIADO INTERNO) - D: [\w ]*. C: (?P<actor>[\w ]+)",
            transaction.memo,
        )
        if _pix_interno_match:
            transaction.memo = _pix_interno_match.group("memo")
            transaction.name = _pix_interno_match.group("actor")


def improve_santander_transaction(transaction: STMTTRN) -> object:
    if "COMPRA CARTAO" in transaction.memo:
        if transaction.memo[35:40] != "":
            transaction.dtposted = datetime.strptime(
                f"{transaction.memo[35:40]}/20 -0300", "%d/%m/%y %z"
            )
            transaction.name = transaction.memo[41:].strip()
    elif (
        "DEBITO AUT." in transaction.memo
        or "REMUNERACAO CONTAMAX" in transaction.memo
    ):
        transaction.name = "Santander"
    else:
        transaction.name = transaction.memo[35:].strip()

    transaction.memo = transaction.memo[:35].strip()


def improve_transactions_format(transactions: TranList, bankid: int):
    transactions.dtstart = fix_time(transactions.dtstart)
    transactions.dtend = fix_time(transactions.dtend)

    for transaction in transactions:
        transaction.dtposted = fix_time(transaction.dtposted)
        transaction.trntype = "PAYMENT" if transaction.trnamt < 0 else "CREDIT"

        if BANK_NAMES[bankid] == "Santander":
            transaction = improve_santander_transaction(transaction)
        elif BANK_NAMES[bankid] == "Inter":
            transaction = improve_inter_transaction(transaction)
