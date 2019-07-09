import flask_restful as restful

from app.attendance.models import Attendance

class AttendanceAPI(restful.Resource):
    def post(self):
        return 201