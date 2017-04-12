#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
.d8888b.                    d8b 888             
d88P  Y88b                   Y8P 888             
Y88b.                            888             
 "Y888b.    8888b.  88888b.  888 888888 888  888 
    "Y88b.     "88b 888 "88b 888 888    888  888 
      "888 .d888888 888  888 888 888    888  888 
Y88b  d88P 888  888 888  888 888 Y88b.  Y88b 888 
 "Y8888P"  "Y888888 888  888 888  "Y888  "Y88888 
                                             888 
                                        Y8b d88P 
                                         "Y88P"  
The Sanity Project - Code to make life easy

DJANGO TOOLS - Date tools

@requires: python-dateutil
@requires: django>=1.4
    

date_now():     
    Gives the current date & time in a timezone aware datetime

date_now(format="%Y-%m-%d %H:%M"):
    Gives the current date & time as a string according to the format you specify using
    strftime syntax.
    e.g. "2017-04-12 20:51"
    
convert_date(datestr):
    Works out what datetime you mean from a string, then returns a timezone aware datetime.
    No more mucking about with strptime!

delta_as_text(datetime1, datetime2)
    Works out how long ago datetime1 was compared to datetime2. Expresses this in human-
    readable terms. i18n safe. If you leave out datetime2, it will compare datetime1 to now.
    e.g. "4 months, 3 days"


"""
from __future__ import unicode_literals
from datetime import timedelta, time, datetime as datetime_dumb
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from django.utils.datetime_safe import datetime
from django.utils.timezone import utc, make_aware, is_naive, get_current_timezone, localtime
from django.utils.translation import ungettext as _PSTAT

ISO8601_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z" #Unbelievably, %z is supported in strftime but not in strptime... Use convert_date instead of strptime


def date_now(local_tz=False, format=None, tz=None):
    """
    Fetches the current date in the current timezone at the moment this function is called.
    Ensures you always get a timezone-aware time for now(). Call this function to guarantee a true now() timestamp
    
    @param local_tz: <bool> or "local" or <Timezone> instance: What timezone to give the now() value in.
                     If True or 1 or "local": uses locale's timezone
                     if a Timezone instance, will use that Timezone
    @keyword format: <string> A strftime representation of what to cast the date into. This means you'll get a string back!!
                     If you supply "ISO", will return it in ISO8601 format (%Y-%m-%dT%H:%M:%S%z), cross-platform capable
    
    @return: <Django datetime> for now() if format not supplied. Timezone aware
             <str> representation of now(), if format IS supplied. Will report the timezone if you ask for it in your formatting rules (e.g. %Z or %z)  
    """
    #The definitive way to get now() in Django as a TZ aware:
    now = datetime_dumb.utcnow().replace(tzinfo=utc)
    
    #In the spirit of consistency, this also takes "tz" as an expression for your timezone
    if not local_tz and tz is not None:
        local_tz = tz
    
    #Has a local_tz expression of a timezone been given?
    if local_tz and str(local_tz) not in ("utc", "UTC"): #Yes there's a local timezone indicated
        #What timezone are they trying to get at? 
        if str(local_tz).lower() == "local" or local_tz in (True, 1, "true"): #Means they want the local timezone
            target_tz = get_current_timezone()
        else: #Means they want some other timezone:
            target_tz = local_tz
        
        #Now convert to the relevant timezone
        if is_naive(now): #Ensures we give a local timezone-aware dt whatever happens
            now = make_aware(now, target_tz) #Wasn't aware. Is now to the local tz
        else:
            now = localtime(now, target_tz)
    
    #If format flag set, strftime it to that format:
    if format:
        if str(format).lower() in ("iso","iso8601"):
            format = ISO8601_DATE_FORMAT
        now = now.strftime(format)
    return now
    

def convert_date(datestr, tz=False):
    """
    Takes datestr, parses it into a date if possible, then makes it timezone aware if lacking
    NB: it assumes the current timezone if a string that maps to a naive datetime is provided
    
    @param datestr: <str> or <datetime> - something which we can try resolve a date from
    @keyword tz: <timezone> or "local" or "utc" - the timezone to assume the date is in.
                 If already timezone aware, will convert it to that timezone
                 If none specified, will use LOCALTIME. 
    
    @return: <Django datetime> timezone-aware date, in the timezone you have specified
    """
    try:
        if isinstance(datestr,(datetime, datetime_dumb)): #First if the item is already a datetime object, don't try to resolve it!!
            datecon = datestr
        else: #Is a string, try to resolve it
            datecon = parse(datestr, fuzzy=True, default=None) #MJTB - 2017-04-12 - Bugfixed to ensure parser doesn't buff out
        if datecon:
            #Check if timezone needs to be made aware:
            if not tz or tz=="local": #DEFAULT TO LOCAL!!
                tz = get_current_timezone()
            elif str(tz).lower()=="utc":
                tz = utc
            if is_naive(datecon):
                #Need to make this timezone aware now!
                datecon = make_aware(datecon, tz)
            else: #Is already timezone aware, so need to convert to the specified timezone
                datecon = localtime(datecon, tz)
            return datecon
        else:
            return False
    except KeyError:
        return False


def get_midnight(dt, offset):
    """
    Return the UTC time corresponding to midnight in local time for the day specified, offset forward by the specified
    number of days (eg. offset=0 -> last midnight, offset=1 -> next midnight etc)
    
    @param dt: <datetime> The datetime you are converting to midnight
    @return: Aware <datetime> 
    """
    current_tz = get_current_timezone()
    local = current_tz.normalize(dt.astimezone(current_tz))        # Convert to local time before processing to get next local midnight
    o = datetime.combine(local + timedelta(days=offset), time(0, 0, 0))
    return make_aware(o, get_current_timezone())

def next_midnight(dt):
    """
    Get the next midnight
    @param dt: <datetime> The datetime you are converting to midnight
    @return: Aware <datetime> 
    """
    return get_midnight(dt, 1)

def last_midnight(dt):
    """
    Get the last midnight
    @param dt: <datetime> The datetime you are converting to midnight
    @return: Aware <datetime> 
    """
    return get_midnight(dt, 0)


def delta_as_text(dt1, dt2=None, tz1="utc", tz2="utc", include="YmdHM", include_zeros=True):
    """
    Tells you how old dt1 is compared to dt2 in translated textual format
    If dt2 is not given, will assume you mean "now".
    
    @param dt1: <Django datetime> or <datetime> or <string> expression of datetime
    @keyword dt2:  <Django datetime> or <datetime> or <string> expression of datetime. If omitted, will use 
    @keyword tz1: <timezone> the timezone to either convert dt1 to, or to assume dt1 is in (if naive)
    @keyword tz2: <timezone> the timezone to either convert dt2 to, or to assume dt1 is in (if naive)
    @keyword include: <string> a description in strftime nomenclature for what elements to include
            Y or y = Years
            m or b or B = months
            d or D = days
            H or h = hours
            M or I or i = minutes
    
    @return: <unicode> representation of the age of dt1 (e.g. "3 years, 2 hours, 1 month, 5 days")
    """
    out_desc = [] #Used to build our output
    
    # Convert dt1 to timezone-aware datetime
    dt1 = convert_date(dt1, tz1)
    # Convert dt2 to timezone-aware datetime
    if dt2:
        dt2 = convert_date(dt2, tz2)
    else:
        dt2 = date_now(local_tz=tz2) #Gets now() in the specified timezone
    
    #Calculate the relative delta:
    delta = relativedelta(dt2, dt1)
    
    #Determine what we want
    do_years = "Y" in include or "y" in include
    do_months = "m" in include or "b" in include or "B" in include #Expressions meaning months
    do_days = "d" in include or "D" in include
    do_hours = "H" in include or "h" in include
    do_minutes = "M" in include or "i" in include or "I" in include
    
    #Build the string components (yes I'm aware we could reduce this to a loop using getattr() on delta)
    if do_years and (include_zeros or delta.years != 0):
        time_years = _PSTAT("%(count)d year", "%(count)d years", delta.years) % {"count":delta.years}
        out_desc.append(time_years)
    if do_months and (include_zeros or delta.months != 0):
        time_months = _PSTAT("%(count)d month", "%(count)d months", delta.months) % {"count":delta.months}
        out_desc.append(time_months)
    if do_days and (include_zeros or delta.days != 0):
        time_days = _PSTAT("%(count)d day", "%(count)d days", delta.days) % {"count":delta.days}
        out_desc.append(time_days)
    if do_hours and (include_zeros or delta.hours != 0):
        time_hours = _PSTAT("%(count)d hour", "%(count)d hours", delta.hours) % {"count":delta.hours}
        out_desc.append(time_hours)
    if do_minutes and (include_zeros or delta.minutes != 0):
        time_minutes = _PSTAT("%(count)d minute", "%(count)d minutes", delta.minutes) % {"count":delta.minutes}
        out_desc.append(time_minutes)
    
    output = u", ".join(out_desc)
    return output
