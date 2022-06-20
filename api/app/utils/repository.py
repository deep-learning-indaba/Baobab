from app import db

class BaseRepository():

    @staticmethod
    def add(model):
        db.session.add(model)
        db.session.commit()
        return model

    @staticmethod
    def save():
        db.session.commit()