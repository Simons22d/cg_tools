from tools import db, ma
from datetime import datetime


class Bike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False)
    branch = db.Column(db.Integer, nullable=False)
    serial_number = db.Column(db.String(100), nullable=False, unique=True)
    date_added = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, plate_number, email, branch, serial_number):
        self.plate_number = plate_number
        self.email = email
        self.branch = branch
        self.serial_number = serial_number


class BikeSchema(ma.Schema):
    class Meta:
        fields = ("id", "plate_number", "email", "branch", "serial_number", "date_added")


class Severity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    weight = db.Column(db.Integer, nullable=False)

    def __init__(self, name, weight):
        self.name = name
        self.weight = weight


class SeveritySchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "weight")


class BranchReports(db.Model):
    """we need to refactor db to add each branch for each of the categrory"""
    id = db.Column(db.Integer, primary_key=True)
    branch = db.Column(db.ForeignKey("branch.id"), nullable=False)
    severity = db.Column(db.ForeignKey('severity.id'), nullable=True)
    category = db.Column(db.ForeignKey("category.id"), nullable=True)
    comments = db.Column(db.Text)
    date_added = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, branch, severity, category, comments):
        self.branch = branch
        self.severity = severity
        self.category = category
        self.comments = comments


class BranchReportsSchema(ma.Schema):
    class Meta:
        fields = ("id", "severity", "category", "comments", "date_added")


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=True)

    def __init__(self, name):
        self.name = name


class CategorySchema(ma.Schema):
    class Meta:
        fields = ("id", "name")


class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True,unique=True)
    name = db.Column(db.String(255), nullable=False, unique=True)

    def __init__(self, name):
        self.name = name


class BranchSchema(ma.Schema):
    class Meta:
        fields = ("id", "name")


class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(255), nullable=False)
    notified = db.Column(db.Boolean, default=0)
    date_added = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, user, notified):
        self.user = user
        self.notified = notified


class ReminderSchema(ma.Schema):
    class Meta:
        fields = ("id", "user", "notified","date_added")


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    branch = db.Column(db.ForeignKey("branch.id"), nullable=False)

    def __init__(self, email, name, branch):
        self.email = email
        self.name = name
        self.branch = branch


class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "email", "name", "branch")
