from app import db
from app.files.models import File 

class FileRepository:
	@staticmethod
	def get_by_id(file_id):
		return db.session.query(File).get(file_id)


	@staticmethod
	def save(file):
	    db.session.add(file)
	    db.session.commit()
	    return file.id