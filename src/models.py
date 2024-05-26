from sqlalchemy import Column, Float, Integer, String

from src.config.database import Base


class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True, index=True)
    state = Column(String, index=True)
    city = Column(String, index=True)
    lat = Column(Float)
    lon = Column(Float)


class Subscriber(Base):
    __tablename__ = "subscribers"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
