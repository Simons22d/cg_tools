from os.path import isfile
from tools import db
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import smtplib, ssl, imaplib
from os.path import isfile
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from tools.models.models import Reminder, User, Branch, BranchReports
from tools import mail
from flask_mail import Message
from flask import jsonify
import numpy as np
import socket
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
    return pd.DataFrame(data).to_excel(f"/home/dev/cargen_reports/files/{filename}.xlsx")


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
    users_to_email_ = np.setdiff1d(users,reports)
    print(users,reports)
    print(users_to_email_)
    print(">>>>>")
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
                email_info(email,"USER",branch,name)
                log(f"Reminded ---> {user_.email} — {user_.branch} — {branch_.name}")
            except socket.gaierror:
                log("No Connection")
    return dict()


def users_list ():
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



