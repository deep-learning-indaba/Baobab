from app import db

class BaseRepository():

    @staticmethod
    def add(model):
        db.session.add(model)
        db.session.commit()
        return model
    
    @staticmethod
    def add_all(models):
        db.session.add_all(models)
        db.session.commit()
        return models

    @staticmethod
    def save():
        db.session.commit()
