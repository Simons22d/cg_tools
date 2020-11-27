from tools import app, db
from flask import request
from tools.utils.utils import get_issue_count, filename, excel
from flask import jsonify, send_from_directory
from flask_sqlalchemy import sqlalchemy

from tools.models.models import Bike, BranchReports, Category, CategorySchema, BikeSchema, BranchReportsSchema, \
    Branch, BranchSchema, Severity, SeveritySchema, User, UserSchema, Reminder, ReminderSchema

from tools.utils.utils import send_mail, remind_users, email_info,user_has_submitted
from flask_mail import Message
from tools import mail
from datetime import datetime

branch_cat_schema = BranchReportsSchema()
branches_cat_schema = BranchReportsSchema(many=True)

category_schema = CategorySchema()
categories_schema = CategorySchema(many=True)

bike_schema = BikeSchema()
bikes_schema = BikeSchema(many=True)

branch_schema = BranchSchema()
branches_schema = BranchSchema(many=True)

severity_schema = SeveritySchema()
severties_schema = SeveritySchema(many=True)

user_schema = UserSchema()
users_schema = UserSchema(many=True)

reminder_schema = ReminderSchema()
reminders_schema = ReminderSchema(many=True)


@app.route('/reports', methods=["POST"])
def hello_world():
    start = request.json["start"]
    end = request.json["end"]
    status = request.json["status"]
    print(start, end, status)

    data = get_issue_count(start, end, status)
    today = filename(start, end, status)

    if data:
        excel(data, today)
        return jsonify({"msg": f"{today}.xlsx"})
    else:
        return jsonify({"msg": None})


@app.route("/reports/download/<string:filename>")
def download(filename):
    return send_from_directory("files", filename=filename)


@app.route("/bike/add", methods=["GET", "POST"])
def add_bike():
    plate_number = request.json["plate_number"]
    email = request.json["email"]
    branch = request.json["branch"]
    serial_number = request.json["serial_number"]

    lookup = Bike(plate_number, email, branch, serial_number)
    db.session.add(lookup)
    db.session.commit()

    return jsonify(bike_schema.dump(lookup))


@app.route("/bike/get/single", methods=["POST", "GET"])
def get_single_bike():
    id = request.json["id"]
    lookup = Bike.query.get(id)
    return jsonify(bike_schema.dump(lookup))


@app.route("/bike/get/all", methods=["POST", "GET"])
def get_all_bikes():
    lookup = Bike.query.all()
    return jsonify(bikes_schema.dump(lookup))


@app.route("/branch/report/add", methods=['POST', 'GET'])
def add_branch_report():
    print("branch report add")
    # get all categories
    categories = Category.query.all()
    branch = request.json["branch"]
    data = request.json["data"]
    for category in categories:
        category_id = int(category.id)
        severity = int(data[category.name.lower()]["severity"])
        comments = data[category.name.lower()]["comments"]

        print(branch,category_id,severity,comments)

        # adding to the DB
        lookup = BranchReports(branch, severity, category_id, comments)
        db.session.add(lookup)
        db.session.commit()

    return jsonify(data)


@app.route("/branch/report/get/single", methods=["GET", "POST"])
def get_single_branch():
    branch_id = request.json["branch_id"]
    lookup = BranchReports.query.get(branch_id)
    return jsonify(branch_cat_schema.dump(lookup))


@app.route("/branch/report/get/all", methods=["POST", "GET"])
def get_all_branches():
    lookup = BranchReports.query.all()
    return jsonify(branches_cat_schema.dump(lookup))


@app.route("/category/seed", methods=["POST"])
def seed_category():
    categories = ["SAP", "ETR", 'Networks', "Emails", "Printers"]
    for category in categories:
        lookup = Category(category)
        db.session.add(lookup)
        db.session.commit()
    return jsonify(categories)


@app.route("/branch/report/category/get/single", methods=["GET", "POST"])
def category_get_single():
    category_id = request.json["id"]
    lookup = Category.query.get(category_id)
    return jsonify(category_schema.ump(lookup))


@app.route("/branch/report/category/get/all", methods=["GET", "POST"])
def category_get_all():
    lookup = Category.query.all()
    return jsonify(categories_schema.dump(lookup))


@app.route("/reports/branch", methods=["GET", "POST"])
def branch_reports():
    """
    > bike reports
    > branch reports
    >
    """
    category = request.json["category"]
    start = request.json["start"]
    end = request.json["end"]
    return jsonify(list())


@app.route("/branch/seed", methods=['POST'])
def seed_branches():
    branches = ["kitengela", "HQ", "nanyuki", "mombasa", "malindi", "voi", "kisumu", 'kitale', 'kisii', 'eldoret',
                'bungoma', 'kericho', 'naruku', 'cummins']
    for branch in branches:
        lookup = Branch(branch.lower().capitalize())
        try:
            db.session.add(lookup)
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            return jsonify({"msg": "Error! Records exists"}), 500
    return jsonify({"msg": "success"}), 201


@app.route("/severity/seed", methods=["GET", "POST"])
def seed_categories():
    categories = [
        {"name": "okay", "weight": 1},
        {"name": "slow", "weight": 2},
        {"name": "not functional", "weight": 3}
    ]

    for category in categories:
        lookup = Severity(category["name"].lower().capitalize(), category["weight"])
        try:
            db.session.add(lookup)
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            return jsonify({"msg": "Error! Categories exists"})
    return jsonify({"msg": "Success! Categories Added Successfully"})


@app.route("/branch/get/all", methods=["POST"])
def get_branches():
    lookup = Branch.query.all()
    return jsonify(branches_schema.dump(lookup))


@app.route("/category/get/all", methods=["POST", "GET"])
def get_categories():
    lookup = Category.query.all()
    return jsonify(categories_schema.dump(lookup))


@app.route("/severity/get/all", methods=["POST", "GET"])
def get_severity():
    lookup = Severity.query.all()
    return jsonify(severties_schema.dump(lookup))


@app.route("/send/email", methods=['POST', 'GET'])
def send_email_():
    from_ = request.json["from"]
    to = request.json["to"]
    subject = request.json["subject"]
    body = request.json["body"]
    return send_mail(from_, to, subject, body)


@app.route('/user/seed', methods=["POST"])
def add_user_seed():
    users = [
        {"email": "denniskiruku@gmail.com", "name": "Denis Kiruku", "branch": 1},
        {"email": "kirukuwambui@gmail.com", "name": "Kiruku Wambui", "branch": 1}
    ]
    for user in users:
        print(user)
        lookup = User(user["email"], user["name"], user["branch"])
        try:
            db.session.add(lookup)
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            return jsonify({"msg": "Error! User exists"})
    return jsonify(user)


@app.route('/user/add', methods=["POST"])
def add_user_():
    name = request.json["name"]
    email_ = request.json["email"]
    branch = request.json["branch"]
    lookup = User(email_,name,branch)
    try:
        db.session.add(lookup)
        db.session.commit()
    except sqlalchemy.exc.IntegrityError:
        return jsonify({"msg": "Error! User exists"})
    return jsonify(user_schema.dump(lookup))


@app.route('/branch/users/get', methods=["GET", "POST"])
def get_branch_users():
    users = User.query.all()
    users_ = users_schema.dump(users)
    print(users_)
    final = list()
    for user in users_:
        branch = Branch.query.get(user["branch"])
        user.update({"branch":branch_schema.dump(branch)["name"]})
        final.append(user)
    return jsonify(final)


@app.route("/branch/user/remove",methods=["GET","POST"])
def remove_user():
    email = request.json["email"]
    data = User.query.filter_by(email=email).first()
    print(data)
    db.session.delete(data)
    db.session.commit()

    return jsonify(user_schema.dump(data))


@app.route("/branch/todays/submit",methods=["POST"])
def get_lastest_update():
    # get all branches
    branches = Branch.query.all()
    date = datetime.now().strftime("%Y-%m-%d")
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
                                    f"ORDER BY brd.date_added DESC LIMIT 5")
        final.append({"name":branch.name,"data" :[dict(row) for row in lookup]})
    return jsonify(final)


@app.route("/branch/todays/submit/single",methods=["POST"])
def get_lastest_update_():
    branch = request.json["branch"]
    date = datetime.now().strftime("%Y-%m-%d")
    # sort last per branch
    lookup = db.session.execute(f"SELECT b.*, brd.* "
                                f"FROM branch b "
                                f"INNER JOIN branch_reports brd "
                                f"ON b.id = brd.branch "
                                f"AND brd.branch = {branch} "
                                f"AND brd.date_added "
                                f"LIKE '%{date}%' "
                                f"ORDER BY brd.date_added DESC")
    return jsonify([dict(row) for row in lookup])



@app.route("/send/email/reminder", methods=["POST"])
def remind():
    return remind_users()


@app.route("/has/submitted",methods=["POST"])
def sdfsdf():
    user = request.json["user_id"]
    return jsonify({'msg': user_has_submitted(user)})



@app.route('/email', methods=["POST"])
def email():
    return send_mail("denis.kiruku@cargen.com", "tests from localhost", "Just like any other body")


@app.route('/email/2', methods=["POST"])
def email_2():
    msg = Message("Tests ....", sender="itsupport@cargen.com", recipients=["denis.kiruku@cargen.com"])
    mail.send(msg)
    return dict()
