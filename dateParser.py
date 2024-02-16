from datetime import datetime, timedelta
import pytz
import dateparser

def parse_date(date_string):
    # Parse the date string using dateparser
    date_object = dateparser.parse(date_string)

    # Convert to IST timezone
    ist = pytz.timezone('Asia/Kolkata')
    ist_date_object = date_object.astimezone(ist)

    # Calculate the time difference
    current_time = datetime.now(ist)
    time_difference = current_time - ist_date_object

    # If message sent within the same minute
    if time_difference.total_seconds() < 60:
        return "Just Now"
    
    # If message sent within the same hour
    elif time_difference.total_seconds() < 3600:
        minutes = int(time_difference.total_seconds() / 60)
        return f"{minutes} mins ago"
    
    # If message sent within the same day
    elif ist_date_object.date() == current_time.date():
        hours = int(time_difference.total_seconds() / 3600)
        return f"{hours} hours ago"

    # If message sent yesterday
    elif current_time - ist_date_object < timedelta(days=1):
        return "Yesterday"

    # If message sent within the same week
    elif current_time - ist_date_object < timedelta(days=7):
        days = int(time_difference.total_seconds() / (3600 * 24))
        return f"{days} days ago"
    
    # Otherwise
    else:
        return ist_date_object.strftime('%d/%m/%Y')