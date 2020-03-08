import uuid
from app import db

class File(db.Model):
	__tablename__ = "file"
	id = db.Column(db.Integer, primary_key=True)
	file_name = db.Column(db.String(50), nullable=False)
	mime_type = db.Column(db.String(50), nullable=False)
	guid = db.Column(db.String(50), nullable=False)

	def __init__(self, file):
		self.file_name = file.filename
		self.mime_type = file.content_type
		self.guid = str(uuid.uuid4().hex)
	