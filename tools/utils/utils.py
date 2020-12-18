from tools import db
import smtplib
import socket
from datetime import datetime
from os.path import isfile

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from flask_mail import Message

from tools import db
from tools import mail
from tools.models.models import User, Branch, BranchReports

from dotmap import DotMap

# in to str mapper
status_mapper = ["New", "Assigned", "Resolved", "Closed", "Escalated", "All"]


def filename(start, end, status):
    start = datetime.strptime(start, '%Y-%m-%d')
    end = datetime.strptime(end, '%Y-%m-%d')
    final = f"{status_mapper[int(status)].upper()} FROM {format_date_no_time(start)} TO {format_date_no_time(end)}"
    return final


def get_issue_count(start, end, status):
    if int(status) == 4:
        # esaclated
        # "SELECT issue.* user.firstname, user.lastname,user.email from " \
        # "issue INNERJOIN issue_assignment ON issue.id = issue_assignment.issue_id INNERJOIN user ON " \
        # "issue_assignment.user_id = user.id;"

        data = db.session.execute(f"SELECT i.*, r.reason "
                                  f"AS reason, u.name "
                                  f"AS employee "
                                  f"FROM issues i "
                                  f"INNER JOIN escalation_requests r "
                                  f"ON r.issue_id = i.id "
                                  f"INNER JOIN users u "
                                  f"ON u.id = r.escalator_id "
                                  f"WHERE r.active = 1")
    elif int(status) == 5:
        # all
        data = db.session.execute(f"select i.*, s.*, er.reason "
                                  f"AS reason, us.name "
                                  f"AS employee "
                                  f"FROM issues i  "
                                  f"LEFT JOIN solutions s "
                                  f"ON s.issue_id = i.id "
                                  f"LEFT JOIN issue_assignments a "
                                  f"ON i.id = a.issue_id "
                                  f"LEFT JOIN escalation_requests er "
                                  f"ON i.id = er.issue_id  "
                                  f"LEFT JOIN users us "
                                  f"ON us.id = er.escalator_id "
                                  f"WHERE i.status < 6 "
                                  f"AND i.dateAdded "
                                  f"BETWEEN '{start} 00:00:00' "
                                  f"AND '{end} 23:59:59' "
                                  f"ORDER BY i.status DESC;")

    else:
        # status
        data = db.session.execute(
            f"SELECT * FROM issues "
            f"WHERE dateAdded "
            f"BETWEEN '{start} 00:00:00' AND '{end} 23:59:00' "
            f"AND status = {status}")

    final = [dict(row) for row in data]

    shell = list()
    priority_mapper = ["", "Low", "Medium", "High"]
    for item in final:
        if not int(item["status"]) == 99 and not (item["dateAdded"] == "None" or item["dateAdded"] == None) and not (
                item["dateUpdated"] == "None" or item["dateUpdated"] == None):
            row = {"ID": item["id"], "TICKET": item["ticket"], "FROM": item["email_from"],
                   "SUBJECT": item["email_subject"], "STATUS": "Escalated" if int(status) == 4 else
                ("Closed" if status == 6 else status_mapper[int(item["status"])]),
                   "BODY": clean(read_file(item["email_body"])), 'NOTIFIED': "Notified" if int(item["notified"]) == 1
                else "Not Notified", "PROIRITY": priority_mapper[int(item["priority"])], "RECEIVED": format_date(
                    item["dateAdded"]), "UPDATED": format_date(item["dateUpdated"])}
            shell.append(row)
            try:
                fin = {
                    "REASON": str(item["reason"]),
                    "EMPLOYEE": str(item["employee"]),
                }
                row.update(fin)
                other = {
                    "PROBLEM": item["problem"],
                    "SOLUTION": item["solution"],
                    "RECOMMENDATION": item["recommendation"]
                }
                row.update(other)
            except KeyError:
                pass
    return shell


def excel(data, filename):
    pd.set_option('display.max_colwidth', 0)
    return pd.DataFrame(data).to_excel(f"/home/dev/cg_tools/tools/files/{filename}.xlsx")


def read_file(filename):
    try:
        if isfile(f"/home/dev/support/email/mails/{filename}"):
            with open(f"/home/dev/support/email/mails/{filename}") as f:
                data = f.read()
                return data
        else:
            return filename
    except FileNotFoundError:
        return "File Not Found"


def clean(data):
    cleantext = BeautifulSoup(data, "html.parser").text
    return cleantext.replace("\n", "").strip().replace("                       ", " ").replace("         ",
                                                                                               " ").replace("     ",
                                                                                                            " ");


def format_date(date):
    final = date.strftime("%a %d %b-%-y %H:%M")
    return str(final)


def format_date_no_time(date):
    final = date.strftime("%a,%d-%b-%-y")
    return str(final)


def report_added_today(date):
    today = datetime.now().strftime("%d%m%Y")
    then = date.strftime("%d%m%Y")
    return then == today


def send_mail(_to, subject, body):
    _from = "itsupport@cargen.com"
    msg = Message(subject, sender="itsupport@cargen.com", recipients=[_to], html=body)
    try:
        mail.send(msg)
    except smtplib.SMTPRecipientsRefused:
        log("email could not email user")
    return dict()


def email_info(_to, kind, branch, user=""):
    # user template kinds
    # date
    branch_ = Branch.query.get(branch)

    date = datetime.now().strftime("%a, %d %b %y.")
    if kind == "ADMIN":
        # subject
        subject = f"Report for {branch} Has Been Recieved."
        body = f'''
        <html>
          <body>
            <p>
                Dear {user},<br>
                {branch} Report for has been recieved.<br>
            </p>
          </body>
        </html>
        '''
        # notification
        send_mail(_to, subject, email_body(body))
    elif kind == "USER":
        # assifned
        subject = f"Branch Report Submit Request For Today {date}"
        body = f'''
               <html>
                 <body>
                   <p>
                       Dear {user},<br><br>
                       
                       Please Follow the link prodived below to .<br>
                       <br>
                       Kindly fill the {branch_.name} Branch report for {date}.

                       <i>This is an automatic message.<br> 
                        <b>Please fill the report form to stop the message from sending.</b> 
                        </i>
                        <br>
                        You can find the form in the following link:<br>
                        <a href="http://192.168.12.200:81/tools/">Link to Form.</a>
                       <br><br>
                       Kind regards <br>
                       IT Support.<br>
                   </p>
                 </body>
               </html>
               '''
        send_mail(_to, subject, email_body(body))
    return list()


def email_body(section):
    return f"""
           <div marginheight="0" marginwidth="0" style="background:#fafafa;color:#222222;font-family:'Helvetica','Arial',sans-serif;font-size:14px;font-weight:normal;line-height:19px;margin:0;min-width:100%;padding:0;text-align:left;width:100%!important" bgcolor="#fafafa">
                                 <table style="background:#fafafa;border-collapse:collapse;border-spacing:0;color:#222222;font-family:'Helvetica','Arial',sans-serif;font-size:14px;font-weight:normal;height:100%;line-height:19px;margin:0;padding:10px;text-align:left;vertical-align:top;width:100%" bgcolor="#fafafa">
                                   <tbody><tr style="padding:0;text-align:left;vertical-align:top" align="left">
                                     <td align="center" valign="top" style="border-collapse:collapse!important;color:#222222;font-family:'Helvetica','Arial',sans-serif;font-size:14px;font-weight:normal;line-height:19px;margin:0;padding:0;text-align:center;vertical-align:top;word-break:break-word">
                                       <center style="min-width:580px;width:100%">
                                         <table style="border-collapse:collapse;border-spacing:0;margin:0 auto;padding:0;text-align:inherit;vertical-align:top;width:580px">
                                           <tbody><tr style="padding:0;text-align:left;vertical-align:top" align="left">
                                             <td style="border-collapse:collapse!important;color:#222222;font-family:'Helvetica','Arial',sans-serif;font-size:14px;font-weight:normal;line-height:19px;margin:0;padding:0;text-align:left;vertical-align:top;word-break:break-word" align="left" valign="top">
                                               <table style="border-collapse:collapse;border-spacing:0;margin-top:20px;padding:0;text-align:left;vertical-align:top;width:100%">
                                                 <tbody><tr style="padding:0;text-align:left;vertical-align:top" align="left">
                                                   <td align="center" style="border-collapse:collapse!important;color:#222222;font-family:'Helvetica','Arial',sans-serif;font-size:14px;font-weight:normal;line-height:19px;margin:0;padding:0;text-align:center;vertical-align:top;word-break:break-word" valign="top">
                                                     <center style="min-width:580px;width:100%">
                                                       <div style="margin-bottom:30px;margin-top:20px;text-align:center!important" align="center !important">
                             <!--                            <img src="https://drive.google.com/file/d/15a4HIX5Lhgwydm03V_GFVMkUT-vsBJRF/view?usp=sharing" width="50" height="48" style="clear:both;display:block;float:none;height:48px;margin:0 auto;max-height:48px;max-width:50px;outline:none;text-decoration:none;width:50px" align="none" class="CToWUd">-->
                                                       </div>
                                                     </center>
                                                   </td>
                                                   <td style="border-collapse:collapse!important;color:#222222;font-family:'Helvetica','Arial',sans-serif;font-size:14px;font-weight:normal;line-height:19px;margin:0;padding:0;text-align:left;vertical-align:top;width:0px;word-break:break-word" align="left" valign="top"></td>
                                                 </tr>
                                               </tbody></table>
                                               <table style="background:#ffffff;border-collapse:collapse;border-radius:3px!important;border-spacing:0;border:1px solid #dddddd;padding:0;text-align:left;vertical-align:top" bgcolor="#ffffff">
                                                 <tbody><tr style="padding:0;text-align:left;vertical-align:top" align="left">
                                                   <td style="border-collapse:collapse!important;color:#222222;font-family:'Helvetica','Arial',sans-serif;font-size:14px;font-weight:normal;line-height:19px;margin:0;padding:0;text-align:left;vertical-align:top;word-break:break-word" align="left" valign="top">

                                                     <div style="color:#333333;font-size:14px;font-weight:normal;line-height:20px;margin:20px">
                             <table style="background:#fff;border-collapse:separate!important;border-spacing:0;box-sizing:border-box;color:#222222;font-family:'Helvetica','Arial',sans-serif;font-size:14px;font-weight:normal;height:100%;line-height:19px;margin:0;padding:10px;text-align:left;vertical-align:top;width:100%" width="100%" bgcolor="#fff">
                                 <tbody><tr style="padding:0;text-align:left;vertical-align:top" align="left">
                                     <td style="border-collapse:collapse!important;box-sizing:border-box;color:#222222;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif,'Apple Color Emoji','Segoe UI Emoji','Segoe UI Symbol';font-size:14px;font-weight:normal;line-height:19px;margin:0;padding:0;text-align:left;vertical-align:top;word-break:break-word" valign="top" align="left"></td>
                                     <td style="border-collapse:collapse!important;box-sizing:border-box;color:#222222;display:block;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif,'Apple Color Emoji','Segoe UI Emoji','Segoe UI Symbol';font-size:14px;font-weight:normal;line-height:19px;margin:0 auto;max-width:580px;padding:24px;text-align:left;vertical-align:top;width:580px;word-break:break-word" width="580" valign="top" align="left">
                                         <div style="box-sizing:border-box;display:block;margin:0 auto;max-width:580px">
                             <table cellpadding="0" cellspacing="0" style="border-collapse:separate!important;border-spacing:0;box-sizing:border-box;margin:0 0 30px;padding:0;text-align:left;vertical-align:top;width:100%" width="100%">
                               <tbody><tr style="padding:0;text-align:left;vertical-align:top" align="left">
                                 <td align="" style="border-collapse:collapse!important;box-sizing:border-box;color:#222222;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif,'Apple Color Emoji','Segoe UI Emoji','Segoe UI Symbol';font-size:14px;font-weight:normal;line-height:19px;margin:0;padding:0;text-align:left;vertical-align:top;word-break:break-word" valign="top">
                                   <table cellpadding="0" cellspacing="0" style="border-collapse:separate!important;border-spacing:0;box-sizing:border-box;padding:0;text-align:left;vertical-align:top;width:auto">
                                     <tbody><tr style="padding:0;text-align:left;vertical-align:top" align="left">
                                       <td style="background:#0366d6;border-collapse:collapse!important;border-radius:5px;box-sizing:border-box;color:#222222;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif,'Apple Color Emoji','Segoe UI Emoji','Segoe UI Symbol';font-size:14px;font-weight:normal;line-height:19px;margin:0;padding:0;text-align:center;vertical-align:top;word-break:break-word" valign="top" bgcolor="#0366d6" align="center">
                                       </td>
                                     </tr>
                                   </tbody></table>
                                 </td>
                               </tr>
                             </tbody></table>

                             <p style="color:#222222;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif,'Apple Color Emoji','Segoe UI Emoji','Segoe UI Symbol';font-size:14px;font-weight:normal;line-height:1.5;margin:0 0 15px;padding:0;text-align:left" align="left">
                                  {section}

                             </p>
                                             <div style="box-sizing:border-box;clear:both;width:100%">
                                                 <hr style="background:#d9d9d9;border-style:solid none none;border-top-color:#e1e4e8;border-width:1px 0 0;color:#959da5;font-size:12px;height:0;line-height:18px;margin:24px 0 30px;overflow:visible">
                                           <div style="box-sizing:border-box;color:#959da5;font-size:12px;line-height:18px">
                                             <p style="color:#959da5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif,'Apple Color Emoji','Segoe UI Emoji','Segoe UI Symbol';font-size:12px;font-weight:normal;line-height:18px;margin:0 0 15px;padding:0;text-align:center" align="center">
                                                     </p>
                                           </div>
                                             </div>
                                         </div>

                                     </td>
                                     <td style="border-collapse:collapse!important;box-sizing:border-box;color:#222222;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif,'Apple Color Emoji','Segoe UI Emoji','Segoe UI Symbol';font-size:14px;font-weight:normal;line-height:19px;margin:0;padding:0;text-align:left;vertical-align:top;word-break:break-word" valign="top" align="left"></td>
                                 </tr>
                             </tbody></table>
                                 </div>
                                       </td>
                                                 </tr>
                                               </tbody></table>

                                               <table style="border-collapse:collapse;border-spacing:0;margin-bottom:30px;padding:0;text-align:left;vertical-align:top;width:100%">
                                                 <tbody><tr style="padding:0;text-align:left;vertical-align:top" align="left">
                                                   <td align="center" style="border-collapse:collapse!important;color:#222222;font-family:'Helvetica','Arial',sans-serif;font-size:14px;font-weight:normal;line-height:19px;margin:0;padding:0;text-align:center;vertical-align:top;word-break:break-word" valign="top">
                                                   </td>
                                                   <td style="border-collapse:collapse!important;color:#222222;font-family:'Helvetica','Arial',sans-serif;font-size:14px;font-weight:normal;line-height:19px;margin:0;padding:0;text-align:left;vertical-align:top;width:0px;word-break:break-word" align="left" valign="top"></td>
                                                 </tr>
                                               </tbody>
                                              </table>
                                             </td>
                                           </tr>
                                         </tbody></table>
                                       </center>
                                     </td>
                                   </tr>
                                 </tbody></table><div class="yj6qo"></div><div class="adL">
                               </div></div><div class="adL">
    """


def remind_users():
    today = datetime.now()
    date = today.strftime("%Y-%m-%d")
    reports_ = [list(row) for row in db.session.execute(f"SELECT DISTINCT branch FROM branch_reports "
                                                        f"WHERE date_added LIKE '%{date}%'")]
    reports = [x[0] for x in reports_]
    users = users_list()
    users_to_email_ = np.setdiff1d(users, reports)
    print(users, reports)
    print(users_to_email_)
    if users_to_email_.any():
        for user in users_to_email_:
            # get user
            user_ = User.query.filter_by(branch=int(user)).first()
            # get the branch assigned
            branch_ = Branch.query.get(int(user))

            name = user_.name
            email = user_.email
            branch = branch_.id
            # send email to usr
            try:
                email_info(email, "USER", branch, name)
                log(f"Reminded ---> {user_.email} — {user_.branch} — {branch_.name}")
            except socket.gaierror:
                log("No Connection")
    return dict()


def users_list():
    users = User.query.all()
    final = list()
    for user in users:
        final.append(user.branch)
    return final


'''
 # if int(report) == int(user.branch):
            # #     # do not email
            # #     log(f"Already Reminded ---> {user.email} — {user.branch} ")
            # #     break
            # # else :
            # #     # email the user
            # #     log(f"Reminded ---> {user.email} — {user.branch} — {report[0]}")
            # #     break
            # else:
                # no reports
                # email all
                # log(f"!!!@@Reminded ALL---> {user.email} — {user.branch}")
        # for user in users:
        #
            # # log("has not submitted")
'''


def user_has_submitted(branch_user_in_charge):
    today = datetime.now()
    date = today.strftime("%Y-%m-%d")
    # date = today.strftime("2020-11-26")
    reports = [dict(row) for row in db.session.execute(f"SELECT * FROM branch_reports WHERE date_added LIKE '%"
                                                       f"{date}%'")]

    if reports:
        for report in reports:
            print(report)
            print(branch_user_in_charge, report["branch"])
            if int(branch_user_in_charge) == int(report["branch"]):
                return True
            else:
                return False
    else:
        return False
    raise Exception("An Error Occured")


def format_date(date) -> int:
    return int(date.strftime("%d%m%y"))


def same_day(date_one, date_two):
    return int(format_date(date_one)) == int(format_date(date_two))


def log(msg):
    print(f"{datetime.now().strftime('%d:%m:%Y %H:%M:%S')} — {msg}")
    return True


def get_by_duration(start, end):
    # BranchReports.date_added.between(datetime.now() + timedelta(days=-2),datetime.now())
    return BranchReports.query.filter(start, end).all()


"""
here we need to use the date as for filter with data weekly context
"""


def get_by_type_branch(type, branch):
    return BranchReports.query.filter(BranchReports.category.contains(type)).filter_by(branch=
        branch).all()


"""
Daily filter needed
"""

def to_list(ResultProxy):
    return [x for x in ResultProxy]

def get_daily_branch(branch,date):
    return db.session.execute(f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND day(date_added) = day("
                              f"'{date}')")


"""
Weekly filter needed
"""


def get_weekly_branch(branch,date):
    return db.session.execute(f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND week(date_added) = week("
                              f"'{date}')")



"""
Monthly filter needed
"""


def get_monthly_branch(branch):
    return db.session.execute(f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND month(date_added) = month("
                              f"'{date}')")


"""
Yearly filter needed
"""


def get_yearly_branch(branch):
    return db.session.execute(f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND year(date_added) = year("
                              f"'{date}')")



"""
get daily report branch -> by type 
"""



"""
Daily filter TYPE needed
"""


def get_daily_branch(branch,date,type):
    return db.session.execute(f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND day(date_added) = day("
                              f"'{date} AND category = {type}')")


"""
Weekly filter TYPE needed
"""


def get_weekly_branch(branch,date,type):
    return db.session.execute(f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND week(date_added) = week("
                              f"'{date}') AND category = {type}")



"""
Monthly filter TYPE needed
"""


def get_monthly_branch(branch,type):
    return db.session.execute(f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND month(date_added) = month("
                              f"'{date} AND category = {type}')")


"""
Yearly filter TYPE needed
"""


def get_yearly_branch(branch,type):
    return db.session.execute(f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND year(date_added) = year('"
                              f"{date}') AND category = {type}'")





"""
working with -> severity
"""

"""
Daily filter TYPE needed
"""

def get_daily_branch(branch, date, severity):
    return to_list(db.session.execute(f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND day(date_added) = day("
                              f"'{date} AND severity = {severity}')"))

"""
Weekly filter TYPE needed
"""

def get_weekly_branch(branch, date, severity):
    return to_list(db.session.execute(f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND week(date_added) = week("
                              f"'{date}') AND severity = {severity}"))

"""
Monthly filter TYPE needed
"""

def get_monthly_branch(branch, date, severity):
    return to_list(db.session.execute(f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND month(date_added) = month('{date}')"
                              f" AND severity = {severity}"))

"""
Yearly filter TYPE needed
"""

def get_yearly_branch(branch, date, severity):
    return to_list(db.session.execute(f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND year(date_added) = year('"
                              f"{date}') AND severity = {severity}"))



"""
SEVERITY and CATEGORY for branch
"""

def get_daily_branch(branch, date, severity, category):
    query = f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND day(date_added) = day('{date}') AND severity = {severity} AND category= {category}"
    print(query)
    return to_list(db.session.execute(query))

"""
Weekly filter TYPE needed
"""

def get_weekly_branch(branch, date, severity,category):
    query = f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND week(date_added) = week('{date}') AND severity = {severity} AND category= {category}"
    print(query)
    return to_list(db.session.execute(query))

"""
Monthly filter TYPE needed
"""

def get_monthly_branch(branch, date, severity,category):
    return to_list(db.session.execute(f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND month(date_added) = month("
                              f"'{date} AND severity = {severity}') AND category= {category}"))

"""
Yearly filter TYPE needed
"""

def get_yearly_branch(branch, date, severity,category):
    return to_list(db.session.execute(f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND year(date_added) = "
                                      f"year('{date}') AND severity = {severity}  AND category= {category}"))



"""
SEVERITY and CATEGORY RANDOM WITH TIME
"""

def get_daily_with_category_and_severity(date, severity, category):
    return to_list(db.session.execute(f"SELECT * FROM  branch_reports WHERE day(date_added) = day('{date}') AND severity = "
                              f"{severity} AND category= {category}"))

"""
Weekly filter TYPE needed
"""

def get_weekly_with_category_and_severity(date, severity, category):
    return to_list(db.session.execute(f"SELECT  * FROM  branch_reports WHERE week(date_added) = week('{date}') AND severity ="
                              f" {severity} AND category = {category}"))

"""
Monthly filter TYPE needed
"""

def get_monthly_with_category_and_severity(date, severity,category):
    return to_list(db.session.execute(f"SELECT  * FROM  branch_reports WHERE month(date_added) = month('{date}') and severity = "
                              f"{severity} AND category = {category}"))

"""
Yearly filter TYPE needed
"""

def get_yearly_with_category_and_severity(date, severity,category):
    return to_list(db.session.execute(f"SELECT  * FROM  branch_reports WHERE year(date_added) = year('{date}') and severity = "
                              f"{severity} AND category = {category}"))

"""
MOST FAILED WEEEKLY IS GOING TO BE: 
1. get the category 'daily,weekly, monthly, yearly'
2. get the count for each of the category
3. get the highest count
"""


"""
Here we need the most failed entity
>> we need to group by to get the most failed branch
"""

duration_mapper_no_branch = {
    "daily" : get_daily_with_category_and_severity,
    "weekly" : get_weekly_with_category_and_severity,
    "monthly" : get_monthly_with_category_and_severity,
    "yearly" : get_yearly_with_category_and_severity
}

duration_mapper_with_branch = {
    "daily" : get_daily_branch,
    "weekly" : get_weekly_branch,
    "monthly" : get_monthly_branch,
    "yearly" : get_yearly_branch
}

categories,names =[x[0] for x in db.session.execute("SELECT id FROM category order by id asc;")],[x[0] for x in
                                                                                                  db.session.execute(
                                                                                                      "SELECT name "
                                                                                                      "FROM category order by id asc;")]

def get_status_by_category_and_duration(date, duration,status):
    """
    1. get all data for the category
    2. compare and return the largest
    :return int
    """
    results = dict()
    try:
        # get the category needed
        func  = duration_mapper_no_branch[duration]
        for index,category in enumerate(categories):
            items = func(date,status,category)
            results.update({names[index] : items.__len__()})
    except KeyError:
        results
    return results



def get_status_by_category_and_branch(branch, date, duration, status):
    """
    1. get all data for the category
    2. compare and return the largest
    :return int
    """
    results = dict()
    try:
        # get the category needed
        func = duration_mapper_with_branch[duration]
        for index,category in enumerate(categories):
            items = func(branch,date,status,category)
            # print(items)
            results.update({names[index] : items.__len__()})
    except KeyError:
        results
    return results


def get_type_by_branch(duration, type):
    return BranchReports.query.filter_by(branch=branch).filter_by(category=type).all()


def maximum_value(dict):
    try:
        return max(dict, key=dict.get)
    except ValueError :
        return "error"


def get_graph_data_per_duration_all(category,date):
    query = f"SELECT * FROM branch_reports WHERE {category.lower()}(date_added) = {category.lower()}({date}) ORDER BY date_added DESC"
    data = db.session.execute(query)
    return format(data)


def get_graph_data_per_duration_branch(category,date,branch):
    query = f"SELECT * FROM branch_reports WHERE {category.lower()}(date_added) = {category.lower()}({date}) AND " \
            f"branch = {branch} ORDER BY date_added DESC"
    data = db.session.execute(query)
    return format(data)


def bootstrap_test():
    data = db.session.execute(f"SELECT ct.name as category, b.name as branch_name, sv.name as severity, br.comments, "
                              f"br.date_added, br.category as cat FROM branch_reports br INNER JOIN branch b ON "
                              f"b.id = br.branch INNER JOIN "
                              f"category ct ON br.category = ct.id INNER JOIN severity sv ON br.severity = sv.id WHERE "
                              f"week(br.date_added) = week('2020-12-18 08:35:39');")
    summary = dict()
    data = format(data)
    for item in data:
        item_ = DotMap(item)
    return data


def format(data):
    return [dict(x) for x in data]

