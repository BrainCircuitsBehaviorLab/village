# mypy: ignore-errors
import dateutil

# import pendulum
# import ciso8601


def parse(date: str):
    return dateutil.parser.parse(date)
    # return pendulum.parse(date)
    # return ciso8601.parse_datetime(date)
