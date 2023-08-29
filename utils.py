import re
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

BRAZIL_TIMEZONE = timezone(timedelta(days=-1, seconds=75600), "GMT")


def fix_time(wrong_datetime: datetime) -> datetime:
    return wrong_datetime.replace(
        hour=0, minute=0, second=0, tzinfo=BRAZIL_TIMEZONE
    )


def prettify_xml(xml: str) -> str:
    _pretty = BeautifulSoup(xml, "xml").prettify()
    return re.compile(">\n\\s+([^<>\\s].*?)\n\\s+</", re.DOTALL).sub(
        ">\\g<1></", _pretty
    )
