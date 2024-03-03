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
    
    

def parse_due_date(date_str):
    # Parse the input date string
    input_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    # Get the current date
    today = datetime.now().date()
    
    # Calculate the difference in days
    delta = input_date - today
    delta_days = delta.days
    
    # Define the messages based on the difference in days
    if delta_days < 0:
        overdue_by = f"Overdue {delta_days}"
        return overdue_by
    elif delta_days == 0:
        return "Today"
    elif delta_days == 1:
        return "Tomorrow"
    elif delta_days < 7:
        return f"{delta_days} Days"
    elif delta_days == 7:
        return "1 Week"
    else:
        return input_date.strftime('%b %d %Y')