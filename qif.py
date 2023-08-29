import re
from typing import Callable

code_to_field = {
    "!": "data_contained",
    "D": "date",
    "T": "amount",
    "U": "amount",
    "M": "memo",
    "N": "ref_number",
    "P": "payee",
    "L": "old_category",
    "C": "cleared",
    "A": "payer_address",
    "F": "reimbursable",
    "S": "split_category",
    "E": "split_memo",
    "$": "split_amount",
    "%": "split_percent",
    "B": "budgeted_amount",
}


def translate_qif_to_json(
    qif_file_path: str, memo_changer: Callable[[str], str]
):
    transactions = []
    curr_transaction = {}

    for line in open(qif_file_path, "r", encoding="cp1252"):
        code = line[0:1]
        value = line[1:].strip()

        if code == "^":
            transactions.append(curr_transaction)
            curr_transaction = {}
        elif code_to_field[code] != "":
            if code == "D" and "'" in value:
                value = re.sub(r"\'(\d+)", "/\\1", value, 0, re.MULTILINE)
            elif code == "M":
                value = memo_changer(value)
            elif code == "T" or code == "$":
                value = float(value.replace(",", ""))
            elif code == "L":
                curr_transaction["category"] = re.sub(
                    f"([^:]+)(:(.+)*)?", "\\1", value, 0, re.MULTILINE
                )
                curr_transaction["sub_category"] = re.sub(
                    f"([^:]+)(:(.+)*)?", "\\3", value, 0, re.MULTILINE
                )
                if len(curr_transaction["sub_category"]) == 0:
                    curr_transaction["sub_category"] = None

            if code_to_field[code] != "old_category":
                curr_transaction[code_to_field[code]] = value

    return transactions
