import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, BigInteger, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine

Base = declarative_base()


class Person(Base):
    __tablename__ = 'person'
    id = Column(BigInteger, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone_number = Column(String(12), nullable=False)
    user_id = Column(Integer, unique=True)
    user_name = Column(String(200), nullable=False)


class Reservation(Base):
    __tablename__ = 'reservation'
    id = Column(BigInteger, primary_key=True)
    date_start = Column(DateTime(True))
    date_end = Column(DateTime(True))
    persons = Column(Integer)
    person_id = Column(Integer, ForeignKey('person.id'))
    person = relationship(Person)
    removed = Column(Boolean, default=False)


# Create an engine that stores data in the local directory's
# sqlalchemy_example.db file.
DB_CONNECTION = os.environ.get('DB_CONNECTION', 'sqlite:///sqlalchemy_example.db')
engine = create_engine(DB_CONNECTION)

# Create all tables in the engine. This is equivalent to "Create Table"
# statements in raw SQL.
Base.metadata.create_all(engine)
