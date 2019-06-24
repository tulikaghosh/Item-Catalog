#!/usr/bin/env python

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Catalog, Base, LatestItem, User

engine = create_engine('sqlite:///categorylist.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
User1 = User(
    name="Tulika Ghosh",
    email="tulikagetsmails@gmail.com",
    picture='https://lh4.googleusercontent.com/-P_-1LGLgU2w/AAAAAAAAAAI/AAAAAAAATOo/qnB7wuZraGs/photo.jpg')
session.add(User1)
session.commit()


# Item for soccer
catalog1 = Catalog(user_id=1, name="Soccer")

session.add(catalog1)
session.commit()

latestItem1 = LatestItem(
    user_id=1,
    name="Shinguards",
    description="Wilson WSP2000 Shin Guards",
    price="$17.99",
    catalog=catalog1)

session.add(latestItem1)
session.commit()


latestItem2 = LatestItem(
    user_id=1,
    name="Soccer Cleats",
    description=" Designed with a classic look, they feature a lightweight, durable synthetic upper for all-game comfort. Made for stability and speed on firm ground.",
    price="$45",
    catalog=catalog1)

session.add(latestItem2)
session.commit()


# Item for snowboarding
catalog2 = Catalog(user_id=1, name="Snowboarding")

session.add(catalog2)
session.commit


latestItem1 = LatestItem(
    user_id=1,
    name="Goggles",
    description="Suitable for prescription glasses underneath, maximum glass size of: 5.51 in length x 1.57 in height.",
    price="$37.99",
    catalog=catalog2)

session.add(latestItem1)
session.commit()

latestItem2 = LatestItem(
    user_id=1,
    name="Snowboard",
    description="This snowboard is appropriate for children ages 5 to 15. It is perfect for entry-level snowboarding, making it a great fit for novice kids.",
    price="$25",
    catalog=catalog2)

session.add(latestItem2)
session.commit()


print "added latest items!"
