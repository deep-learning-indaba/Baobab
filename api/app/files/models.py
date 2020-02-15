import uuid
from app import db

class File(db.Model):
	__tablename__ = "file"
	id = db.Column(db.Integer, primary_key=True)
	file_name = db.Column(db.String(50), unique=True, nullable=False)
	mime_type = db.Column(db.String(20), nullable=False)
	guid = db.Column(db.String(50), unique=True, nullable=False)

	def __init__(self, file_name, mime_type):
		self.file_name = file_name
		self.mime_type = mime_type
		self.guid = str(uuid.uuid4().hex)
	