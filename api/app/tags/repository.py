from app import db
from app.tags.models import Tag, TagTranslation

class TagRepository():

    @staticmethod
    def get_by_id(id):
        return db.session.query(Tag).get(id)

    @staticmethod
    def add_tag(tag):
        db.session.add(tag)
        db.session.commit()
        return tag

    @staticmethod
    def delete_translation(id):
        db.session.query(TagTranslation).filter_by(id=id).delete()

    @staticmethod
    def commit():
        db.session.commit()