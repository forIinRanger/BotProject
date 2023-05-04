import sqlalchemy
from sqlalchemy import orm

from data.db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True,
                           nullable=True)
    state = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True,
                              nullable=True)
    news = orm.relationship("Website", back_populates='user')
