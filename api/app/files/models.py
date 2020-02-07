from app import db

class File(db.Model):
	__tablename__ = "file"
	id = db.Column(db.Integer, primary_key=True)
	file_name = db.Column(db.String(50), unique=True, nullable=False)
	mime_type = db.Column(db.String(20), nullable=False)
	guid = db.Column(db.String(50), unique=True, nullable=False)
	