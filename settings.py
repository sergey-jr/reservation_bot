import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db import Base

BOT_TOKEN = os.environ.get('TOKEN', None)
MAX_SLOTS = int(os.environ.get('MAX_SLOTS', 0))
DB_CONNECTION = os.environ.get('DB_CONNECTION', 'sqlite:///sqlalchemy_example.db')

engine = create_engine(DB_CONNECTION)
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()
