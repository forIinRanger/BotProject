import sqlalchemy
from sqlalchemy import orm

from data.db_session import SqlAlchemyBase


class Website(SqlAlchemyBase):
    __tablename__ = 'websites'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True,
                           nullable=True)
    address = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    climb = sqlalchemy.Column(sqlalchemy.BOOLEAN, nullable=True)
    version = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    user = orm.relationship('User')