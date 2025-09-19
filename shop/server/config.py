import os

basedir = os.path.abspath(os.path.dirname(__file__))
instance_dir = os.path.join(basedir, 'instance')

class Config:
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(instance_dir, 'shop.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
