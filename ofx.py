from typing import TypedDict
from ofxtools.Parser import OFXTree
from ofxtools.header import make_header
from ofxtools.models.ofx import OFX
from ofxtools.models.base import Aggregate
import xml.etree.ElementTree as ElementTree
from improve_bank_transactions import improve_transactions_format, BANK_NAMES
from utils import fix_time, prettify_xml


class Ofx(TypedDict):
    signonmsgsrsv1: TypedDict
    y: int
    label: str


def parse_ofx(filename: str) -> OFX | Aggregate:
    parser = OFXTree()
    parser.parse(filename)
    ofx = parser.convert()

    if parser.getroot().tag != "OFX":
        raise Exception("Isn't an OFX!")

    return ofx


def improve_ofx(ofx: OFX | Aggregate) -> OFX | Aggregate:
    ofx.signonmsgsrsv1.sonrs.dtserver = fix_time(
        ofx.signonmsgsrsv1.sonrs.dtserver
    )

    statement = ofx.statements[0]
    statement.balance.dtasof = fix_time(statement.balance.dtasof)
    improve_transactions_format(
        statement.transactions, int(statement.account.bankid)
    )

    return ofx


def ofx_file_to_json(filename: str) -> object:
    ofx = parse_ofx(filename)
    ofx = improve_ofx(ofx)

    statement = ofx.statements[0]

    formated_transactions = []
    for transaction in statement.transactions:
        formated_transactions.append(
            {
                "id": transaction.fitid,
                "type": transaction.trntype,
                "date": transaction.dtposted,
                "amount": transaction.trnamt,
                "receiver"
                if transaction.trnamt < 0
                else "sender": transaction.name,
                "memo": transaction.memo,
            }
        )

    return {
        "currency": statement.curdef,
        "bank": {
            "name": BANK_NAMES[int(statement.account.bankid)],
            "id": statement.account.bankid,
            "account": {
                "id": int(statement.account.acctid),
                "type": statement.account.accttype,
            },
        },
        "balance": {
            "value": statement.balance.balamt,
            "date": statement.balance.dtasof,
        },
        "transactions": {
            "startdate": statement.transactions.dtstart,
            "enddate": statement.transactions.dtend,
            "list": formated_transactions,
        },
    }


def improve_ofx_file(filename: str):
    ofx = parse_ofx(filename)
    ofx = improve_ofx(ofx)

    ofx_header = str(make_header(version=102))
    ofx_payload = prettify_xml(ElementTree.tostring(ofx.to_etree()).decode())
    ofx_improved = ofx_header + ofx_payload

    open(filename, "w", encoding="utf8", newline="\n").write(ofx_improved)
