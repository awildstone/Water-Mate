from datetime import date, datetime
import pytz
from tzlocal import get_localzone
from zoneinfo import ZoneInfo


ALL_TIMEZONES = pytz.common_timezones

# # current_date = datetime.now()
# # from_zone = get_localzone()
# # current_date.replace(tzinfo=from_zone)

# def get_UTC_offset(datetime_aware_date):
#     print('DATE AWARE TZ NAME')
#     from_zone = date_aware.tzname
#     print(from_zone)
#     for tz in ALL_TIMEZONES:
#         print(tz)
#         # print('############## CURRENT TIMEZONE ##############')
#         # print(tz)
#         # print('############## CURRENT DATE ##############')
#         # to_zone = pytz.timezone(tz)
#         # date_converted = current_date.astimezone(to_zone)
#         # print(date_converted)
#         # print('############## UTC OFFSET ##############')
#         # print(datetime.now(pytz.timezone(tz)).strftime('%z'))


# date = datetime(2021, 5, 1)
# tz = get_localzone()

# date_aware = tz.localize(date)

# get_UTC_offset(date_aware)

# from_zone = ZoneInfo('UTC')
# to_zone = get_localzone()

# date = datetime(2021, 5, 1, 12, 49, tzinfo=from_zone)

# date.astimezone(to_zone)

# print(date.astimezone(to_zone))


# Python program to convert time
# from 12 hour to 24 hour format
# Function to convert the date format
def convert24(string):

    # Checking if last two elements of time
    # is PM and first two elements are 12   
    if string[-2:] == "PM" and string[:2] == "12":
        return string[:-2]
      
    # Checking if last two elements of time
    # is AM and first two elements are 12
    if string[-2:] == "AM" and string[:2] == "12":
        return "00" + string[2:-2]
          
    # remove the AM    
    if string[-2:] == "AM":
        return string[:-2]
      
    # Checking if last two elements of time
    # is PM and first two elements are 12   
    if string[-2:] == "PM" and string[:2] == "12":
        return string[:-2]
          
    else:
        # add 12 to hours and remove PM
        return str(int(string[:2]) + 12) + string[2:8]
  
# Driver Code    
time = "8:50:35 PM"

if time[1] == ":":
    length = len(time)
    new_string = time.zfill(length + 1)
    print(convert24(new_string))
else:
    print(convert24(time))