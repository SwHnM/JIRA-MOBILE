import dateparser
import pytz

def parse_date(date_string):
    # Parse the date string using dateparser
    date_object = dateparser.parse(date_string)

    # Convert to IST timezone
    ist = pytz.timezone('Asia/Kolkata')
    ist_date_object = date_object.astimezone(ist)

    # Format the date into "DD/MM/YYYY HH:MM:SS IST" format
    formatted_date = ist_date_object.strftime('%H:%M %Z %d/%m/%Y ')

    return formatted_date