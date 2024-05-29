from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_collector = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)  # Novo atributo
    identity_photo = Column(String, nullable=True)

    locations = relationship("DonationLocation", back_populates="collector")

class DonationLocation(Base):
    __tablename__ = 'donation_locations'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(String)
    hygiene = Column(Boolean, default=False)
    food = Column(Boolean, default=False)
    clothes = Column(Boolean, default=False)
    collector_id = Column(Integer, ForeignKey('users.id'))

    collector = relationship("User", back_populates="locations")
