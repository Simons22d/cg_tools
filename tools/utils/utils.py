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
import imgkit
from datauri import DataURI
from tools import app

from dotmap import DotMap
import base64
from PIL import Image
from io import BytesIO

# in to str mapper
status_mapper = ["New", "Assigned", "Resolved", "Closed", "Escalated", "All"]

report_css = """ *, *:before, *:after {box-sizing: border-box;}
            
            /* STANDARD ELEMENTS */
            body {
              background: #fff;
              color: #2e3031;
              font: 100%/1.5 "Clan OT", "HelveticaNeue", "Helvetica", "Arial", sans-serif;
              -webkit-text-size-adjust: 100%;
              min-height: 100vh;
              /* Force Outlook to provide a "view in browser" button. */
              width: 100% !important;
              max-width: 950px;
              margin: 0 auto;
            }
            p {
              margin-top: 0;
            }
            img {
              outline: none;
              text-decoration: none;
              display: block;
            }
            br,
            strong br,
            b br,
            em br,
            i br {
              line-height: 100%;
            }
            /* Preferably not the same color as the normal header link color. There is limited support for psuedo classes in email clients, this was added just for good measure. */
            table td,
            table tr {
              border-collapse: collapse;
            }
            table {
              table-layout: fixed;
            }
            /* Body text color for the New Yahoo.  This example sets the font of Yahoo's Shortcuts to black. */
            /* This most probably won't work in all email clients. Don't include code blocks in email. */
            code {
              white-space: normal;
              word-break: break-all;
            }
            
            /* CUSTOM CLASSES */
            .email-body {
              padding: 10px 10px 0;
              background-color: #ffffff;
              border-collapse: collapse;
              border: 0;
              padding: 0;
            }
            
            .header--marketing {
              border-bottom: 8px solid #ffcf00;
            }
            
            .email-content {
              padding: 0 24px 24px;
            }
            .h2, h2 {
              font-size: 24px;
              font-weight: bold;
              margin: .5em 0;
            }
            
            .tablesaw {
              width: 100%;
              max-width: 100%;
              empty-cells: show;
              border-collapse: collapse;
              border: 0;
              padding: 0;
            }
            
            .tablesaw-stack td .tablesaw-cell-label,
            .tablesaw-stack th .tablesaw-cell-label {
              display: none;
            }
            
            .icon {
              display: inline-block;
              margin-left: 4px;
            }
            
            /*#Unsubscribe-Message {color: #767673; white-space: normal; padding-top: 20px;font-size: 11px;}*/
            #Unsubscribe-Message {
              text-decoration: underline !important;
              cursor: pointer;
              padding-left: 50px !important;
              color: #4d95f5;
            }
            
            
            .footer {
              padding: 12px 24px;
              background: #2e3031;
              color: #fff;
              line-height: 1.2;
            }
            .footer__legal {
              font-size: 12px;
              line-height: 16px;
              color: #767673;
              white-space: normal;
            }
            .footer__legal {
              margin: 0;
            }
            /*footer logo section NOT image*/
            .footer-logo {
              // padding: 10px 0 0 50px;
            }
            /*footer logo image NOT section*/
            .logo {
              margin: 0 0 10px;
              max-width: 120px;
              transition: max-width 0.2s ease;
            }
            /**
             * vCard - address and telephone pattern
             */
            .vcard {
              display: inline-block;
              margin-right: 12px;
            }
            .vcard__link {
              color: #767673;
            
              &:hover {
                color: #ffffff;
              }
            }
            .vcard__adr {
              font-size: 12px;
            }
            .vcard__adr > * {
              margin-bottom: 4px;
            }
            .vcard__tel {
              font-size: 12px;
              color: #767673;
            }
            .adr__region {
              border-bottom: none;
            }
            .adr__country-name {
              visibility: hidden;
              height: 0;
            }
            
            
            
            /* Mobile first styles: Begin with the stacked presentation at narrow widths */
            /* Support note IE9+: @media only all */
            @media only all {
              /* Show the table cells as a block level element */
            
              .tablesaw-stack {
                clear: both;
                border-collapse: collapse;
              }
              
              .tablesaw-stack tbody tr {
                // display: block;
                width: 100%;
                border-bottom: 1px solid #dfdfdf;
              }
            
              .tablesaw-stack td,
              .tablesaw-stack th {
                text-align: left;
                display: block;
                font-size: 14px;
              }
            
              .tablesaw-stack th {
                border-bottom: 1px solid #dfdfdf;
                padding: 0;
                border-collapse: separate;
                border-spacing: 10px;
              }
              
              .tablesaw-stack tr {
                clear: both;
                display: table-row;
              }
            
              .tablesaw-stack tr:first-child td {
                padding-top: 8px;
              }
            
              /* Make the label elements a percentage width */
            
              .tablesaw-stack td .tablesaw-cell-label,
              .tablesaw-stack th .tablesaw-cell-label {
                display: inline-block;
                padding: 0 0.6em 0 0;
                width: 30%;
              }
            
              /* For grouped headers, have a different style to visually separate the levels by classing the first label in each col group */
            
              .tablesaw-stack th .tablesaw-cell-label-top,
              .tablesaw-stack td .tablesaw-cell-label-top {
                display: block;
                padding: 0.4em 0;
                margin: 0.4em 0;
              }
            
              .tablesaw-cell-label {
                display: block;
              }
              
              .tablesaw-cell-content {
                display: inline-block;
                max-width: 100%;
              }
              /* Avoid double strokes when stacked */
            
              .tablesaw-stack tbody th.group {
                margin-top: -1px;
              }
            
              /* Avoid double strokes when stacked */
            
              .tablesaw-stack th.group b.tablesaw-cell-label {
                display: none !important;
              }
            }
            
            /* SMALL SCREENS UP TO 660px */
            @media only screen and (max-width: 41.25em) {
            
            }
            
            @media (max-width: 39.9375em) {
              /* Table rows have a gray bottom stroke by default */
            
              .tablesaw-stack tbody tr {
                display: block;
                width: 100%;
              }
            
              .tablesaw-stack thead td,
              .tablesaw-stack thead th {
                display: none;
              }
            
              .tablesaw-stack tbody td,
              .tablesaw-stack tbody th {
                display: block;
                float: left;
                clear: left;
                width: 100%;
              }
            
              .tablesaw-cell-label {
                vertical-align: top;
              }
            
              .tablesaw-cell-content {
                display: inline-block;
                /*max-width: 67%;*/
              }
            
              .tablesaw-stack .tablesaw-stack-block .tablesaw-cell-label,
              .tablesaw-stack .tablesaw-stack-block .tablesaw-cell-content {
                display: block;
                width: 100%;
                max-width: 100%;
                padding: 0;
              }
            
              .tablesaw-stack td:empty,
              .tablesaw-stack th:empty {
                display: none;
              }
            }
            
            /* Media query to show as a standard table at 560px (35em x 16px) or wider */
            @media (min-width: 40em) {
              .tablesaw-stack tr {
                display: table-row;
              }
            
              /* Show the table header rows */
            
              .tablesaw-stack td,
              .tablesaw-stack th,
              .tablesaw-stack thead td,
              .tablesaw-stack thead th {
                display: table-cell;
                margin: 0;
                padding: 4px 8px;
                font-size: 16px;
              }
            
              /* Hide the labels in each cell */
            
              .tablesaw-stack td .tablesaw-cell-label,
              .tablesaw-stack th .tablesaw-cell-label {
                display: none !important;
              }
            }

            @media (max-width: 39.9375em) {
              /* Table Label for document name */
              #Doc_name {
                display: block !important;
              }
            }

            @media (min-width: 40em) {
              #Doc_name {
                display: none !important;
              }
            }

            @media all and (min-width: 52em) {
              h2,
              .h2 {
                font-size: 36px;
              }
              .footer {
                padding: 24px 48px;
              }
            }




            /* Email Client-specific Styles */
            #outlook a {
              padding: 0;
            }

            /*what are the following for?*/
            .article-content,
            #left-sidebar {
              -webkit-text-size-adjust: 90% !important;
              -ms-text-size-adjust: 90% !important;
            }
            .ReadMsgBody {
              width: 100%;
            }
            .ExternalClass {
              width: 100%;
              display: block !important;
            }
            #permission-reminder {
              white-space: normal;
            }"""


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


def send_mail(_to, subject, body,attachment):
    _from = "itsupport@cargen.com"
    msg = Message(subject, sender="itsupport@cargen.com", recipients=[_to], html=body)
    if attachment:
        with app.open_resource(f"../{attachment}.png") as fp:
            msg.attach(f"{attachment}.png", "image/png", fp.read())
    try:

        mail.send(msg)
    except smtplib.SMTPRecipientsRefused as e:
        log("email could not email user")
        log(e)
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
                       
                       Please Follow the link provided below.<br>
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
            except socket.gaierror as e:
                log(f"FAILED ---> {user_.email} — {user_.branch} — {branch_.name}")
                log("No Connection")
    return dict()


def users_list():
    users = User.query.all()
    final = list()
    for user in users:
        final.append(user.branch)
    return final


def daily_report_data():
    # get all branches
    branches = Branch.query.all()
    date = datetime.now().strftime("%Y-%m-%d")
    date_ = datetime.now().strftime("%A, %d %b %Y")
    # final dict
    final = list()
    for branch in branches:
        lookup = db.session.execute(f"SELECT b.*, brd.* "
                                    f"FROM branch b "
                                    f"INNER JOIN branch_reports brd "
                                    f"ON b.id = brd.branch "
                                    f"AND brd.branch = {branch.id} "
                                    f"AND brd.date_added "
                                    f"LIKE '%{date}%' "
                                    f"ORDER BY brd.date_added DESC LIMIT 6")
        lookup = [dict(row) for row in lookup]
        final.append({"name": branch.name, "data": lookup})

    res = {"reports": final, "date": date_}
    return res


import os


def email_report_body(image):
    body = f"""
            <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Document</title>
    </head>
    <body>
    Dear All,<br><br>
    Please find the daily branch reports attached.
    <br>
    Kind Regards,<br>
    IT Support.    
</body>
</html>
    """
    return body


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


def get_daily_branch(branch, date):
    return db.session.execute(f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND day(date_added) = day("
                              f"'{date}')")


"""
Weekly filter needed
"""


def get_weekly_branch(branch, date):
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


def get_daily_branch(branch, date, type):
    return db.session.execute(f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND day(date_added) = day("
                              f"'{date} AND category = {type}')")


"""
Weekly filter TYPE needed
"""


def get_weekly_branch(branch, date, type):
    return db.session.execute(f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND week(date_added) = week("
                              f"'{date}') AND category = {type}")


"""
Monthly filter TYPE needed
"""


def get_monthly_branch(branch, type):
    return db.session.execute(f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND month(date_added) = month("
                              f"'{date} AND category = {type}')")


"""
Yearly filter TYPE needed
"""


def get_yearly_branch(branch, type):
    return db.session.execute(f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND year(date_added) = year('"
                              f"{date}') AND category = {type}'")


"""
working with -> severity
"""

"""
Daily filter TYPE needed
"""


def get_daily_branch(branch, date, severity):
    return to_list(
        db.session.execute(f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND day(date_added) = day("
                           f"'{date} AND severity = {severity}')"))


"""
Weekly filter TYPE needed
"""


def get_weekly_branch(branch, date, severity):
    return to_list(
        db.session.execute(f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND week(date_added) = week("
                           f"'{date}') AND severity = {severity}"))


"""
Monthly filter TYPE needed
"""


def get_monthly_branch(branch, date, severity):
    return to_list(db.session.execute(
        f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND month(date_added) = month('{date}')"
        f" AND severity = {severity}"))


"""
Yearly filter TYPE needed
"""


def get_yearly_branch(branch, date, severity):
    return to_list(
        db.session.execute(f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND year(date_added) = year('"
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


def get_weekly_branch(branch, date, severity, category):
    query = f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND week(date_added) = week('{date}') AND severity = {severity} AND category= {category}"
    print(query)
    return to_list(db.session.execute(query))


"""
Monthly filter TYPE needed
"""


def get_monthly_branch(branch, date, severity, category):
    return to_list(
        db.session.execute(f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND month(date_added) = month("
                           f"'{date} AND severity = {severity}') AND category= {category}"))


"""
Yearly filter TYPE needed
"""


def get_yearly_branch(branch, date, severity, category):
    return to_list(db.session.execute(f"SELECT  * FROM  branch_reports WHERE branch = {branch} AND year(date_added) = "
                                      f"year('{date}') AND severity = {severity}  AND category= {category}"))


"""
SEVERITY and CATEGORY RANDOM WITH TIME
"""


def get_daily_with_category_and_severity(date, severity, category):
    return to_list(
        db.session.execute(f"SELECT * FROM  branch_reports WHERE day(date_added) = day('{date}') AND severity = "
                           f"{severity} AND category= {category}"))


# SELECT * FROM  branch_reports WHERE day(date_added) = day('2020-12-21 05:53:12') AND severity = 1 AND category= 1
"""
Weekly filter TYPE needed
"""


def get_weekly_with_category_and_severity(date, severity, category):
    return to_list(
        db.session.execute(f"SELECT  * FROM  branch_reports WHERE week(date_added) = week('{date}') AND severity ="
                           f" {severity} AND category = {category}"))


"""
Monthly filter TYPE needed
"""


def get_monthly_with_category_and_severity(date, severity, category):
    return to_list(
        db.session.execute(f"SELECT  * FROM  branch_reports WHERE month(date_added) = month('{date}') and severity = "
                           f"{severity} AND category = {category}"))


"""
Yearly filter TYPE needed
"""


def get_yearly_with_category_and_severity(date, severity, category):
    return to_list(
        db.session.execute(f"SELECT  * FROM  branch_reports WHERE year(date_added) = year('{date}') and severity = "
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
    "daily": get_daily_with_category_and_severity,
    "weekly": get_weekly_with_category_and_severity,
    "monthly": get_monthly_with_category_and_severity,
    "yearly": get_yearly_with_category_and_severity
}

duration_mapper_with_branch = {
    "daily": get_daily_branch,
    "weekly": get_weekly_branch,
    "monthly": get_monthly_branch,
    "yearly": get_yearly_branch
}

categories, category_names = [x[0] for x in db.session.execute("SELECT id FROM category order by id asc;")], [x[0] for x
                                                                                                              in
                                                                                                              db.session.execute(
                                                                                                                  "SELECT name "
                                                                                                                  "FROM category order by id asc;")]

branches, branch_names = [x[0] for x in db.session.execute("SELECT id FROM branch order by id asc;")], [x[0] for x in
                                                                                                        db.session.execute(
                                                                                                            "SELECT name "
                                                                                                            "FROM branch "
                                                                                                            "order by id asc;")]


def get_status_by_category_and_duration(date, duration, status):
    """
    1. get all data for the category
    2. compare and return the largest
    :return int
    """
    results = dict()
    try:
        # get the category needed
        func = duration_mapper_no_branch[duration]
        for index, category in enumerate(categories):
            items = func(date, status, category)
            results.update({category_names[index]: items.__len__()})
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
        for index, category in enumerate(categories):
            items = func(branch, date, status, category)
            # print(items)
            results.update({category_names[index]: items.__len__()})
    except KeyError:
        results
    return results


def get_type_by_branch(duration, type):
    return BranchReports.query.filter_by(branch=branch).filter_by(category=type).all()


def maximum_value(dict):
    try:
        return max(dict, key=dict.get)
    except ValueError:
        return "error"


def get_graph_data_per_duration_all(category, date):
    query = f"SELECT * FROM branch_reports WHERE {category.lower()}(date_added) = {category.lower()}({date}) ORDER BY date_added DESC"
    data = db.session.execute(query)
    return format_dict(data)


def get_graph_data_per_duration_branch(category, date, branch):
    query = f"SELECT * FROM branch_reports WHERE {category.lower()}(date_added) = {category.lower()}({date}) AND " \
            f"branch = {branch} ORDER BY date_added DESC"
    data = db.session.execute(query)
    return format_dict(data)


category_map = {x: 0 for x in category_names}


def bootstrap_test():
    # data = db.session.execute(f"SELECT ct.name as category, b.name as branch_name, sv.name as severity, br.comments, "
    #                           f"br.date_added FROM branch_reports br INNER JOIN branch b ON b.id = br.branch "
    #                           f"INNER JOIN category ct ON br.category = ct.id INNER JOIN severity sv ON br.severity = "
    #                           f"sv.id WHERE week(br.date_added) = week('2020-12-18 08:35:39') AND br.category = ct.id "
    #                           f"AND b.id= 7 AND sv.id = 2;")

    # get branches
    # get cateories
    final = dict()
    for branch in branches:
        for category in categories:
            data = db.session.execute(f"SELECT ct.name as category, sv.name as severity, b.name as branch_name "
                                      f"FROM branch_reports br INNER JOIN branch b "
                                      f"ON b.id = br.branch INNER JOIN category ct ON br.category = ct.id INNER JOIN "
                                      f"severity sv ON br.severity = sv.id WHERE week(br.date_added) = "
                                      f"week('2020-12-17 08:35:39') AND br.category = ct.id and ct.id= {category} and "
                                      f"b.id = {branch};")
            # final.update({branch_names[branch-1]:format_dict(data)})
            format_(data)

    print(category_map)

    # remaping data

    # summary = dict()
    # data = format(data)
    # for item in data:
    #     item_ = DotMap(item)
    return final


def format_dict(data):
    return [dict(x) for x in data]


def format_(data):
    for x in data:
        # print(x)
        for category in category_names:
            if str(x[0]) == str(category):
                print(str(category))
                current_value = category_map[category]
                current_value = current_value + 1
                category_map[category] = current_value


def format_list(data):
    return [list(x) for x in data]


def success_icon():
    return """
    data:image/png;base64,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
    """


def slow_icon():
    return """
    data:image/png;base64,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
    """


def error_icon():
    return """
    data:image/png;base64,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
    """


def reports_image(link_ip):
    imgkit.from_url(f"http://{link_ip}:9000/daily/report", 'out.jpg')
    png_uri = DataURI.from_file('out.png')
    return str(png_uri)
