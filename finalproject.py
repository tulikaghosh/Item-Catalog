#!/usr/bin/env python

from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Catalog, LatestItem
from flask import session as login_session
import random, string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Item Application"

engine = create_engine('sqlite:///categorylist.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return "The current session state is %s" % login_session['state']

	
@app.route('/catalog/<int:catalog_id>/latest/JSON')
def catalogLatestJSON(catalog_id):
    catalog = session.query(Catalog).filter_by(id=catalog_id).one()
    items = session.query(LatestItem).filter_by(
        catalog_id=catalog_id).all()
    return jsonify(LatestItems=[i.serialize for i in items])


@app.route('/catalog/<int:catalog_id>/latest/<int:latest_id>/JSON')
def latestItemJSON(catalog_id, latest_id):
    Latest_Item = session.query(LatestItem).filter_by(id=latest_id).one()
    return jsonify(Latest_Item=Latest_Item.serialize)


@app.route('/catalog/JSON')
def catalogJSON():
    catalogs = session.query(Catalog).all()
    return jsonify(calalogs=[r.serialize for r in calalogs])
	
	
	
# Show all catalog
@app.route('/')
@app.route('/catalog/')
def showCatalogs():
    catalogs = session.query(Catalog).all()
    # return "This page will show all catalogs"
    return render_template('catalogs.html',catalogs=catalogs)
	
# Create a new catalog
@app.route('/catalog/new/', methods=['GET', 'POST'])
def newCatalog():
    if request.method == 'POST':
        newCatalog = Catalog(name=request.form['name'])
        session.add(newCatalog)
        flash('New Catalog %s Successfully Created' % newCatalog.name)                                                                                                   
	
        session.commit()
        return redirect(url_for('showCatalogs'))
    else:
        return render_template('newCatalog.html')
    # return "This page will be for making a new catalog"

# Edit a catalog


@app.route('/catalog/<int:catalog_id>/edit/', methods=['GET', 'POST'])
def editCatalog(catalog_id):
    editedCatalog = session.query(
        Catalog).filter_by(id=catalog_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedCatalog.name = request.form['name']
            flash('Catalog Successfully Edited %s' % editedCatalog.name)
			
            return redirect(url_for('showCatalogs'))
    else:
        return render_template(
            'editCatalog.html', catalog=editedCatalog)

    # return 'This page will be for editing catalog %s' % catalog_id

# Delete a catalog


@app.route('/catalog/<int:catalog_id>/delete/', methods=['GET', 'POST'])
def deleteCatalog(catalog_id):
    catalogToDelete = session.query(
        Catalog).filter_by(id=catalog_id).one()
    if request.method == 'POST':
        session.delete(catalogToDelete)
        flash('%s Successfully Deleted' % deleteCatalog.name)
        session.commit()
        return redirect(
            url_for('showCatalogs', catalog_id=catalog_id))
    else:
        return render_template(
            'deleteCatalog.html', catalog=catalogToDelete)
    # return 'This page will be for deleting catalog %s' % catalog_id


# Show a calalog list
@app.route('/catalog/<int:catalog_id>/')
@app.route('/catalog/<int:catalog_id>/list/')
def showList(catalog_id):
    catalog = session.query(Catalog).filter_by(id=catalog_id).one()
    items = session.query(LatestItem).filter_by( catalog_id=catalog_id).all()
    return render_template('list.html', items=items, catalog=catalog)
   
# Create a new latest item
@app.route(
    '/catalog/<int:catalog_id>/list/new/', methods=['GET', 'POST'])
def newLatestItem(catalog_id):
    if request.method == 'POST':
        newItem = latestItem(name=request.form['name'], description=request.form[
                           'description'], price=request.form['price'], catalog_id=catalog_id)
        session.add(newItem)
        flash('New list %s Item Successfully Created' % (newItem.name))
        session.commit()

        return redirect(url_for('showList', catalog_id=catalog_id))
    else:
        return render_template('newlatestitem.html', catalog_id=catalog_id)

# Edit a latest item
@app.route('/catalog/<int:catalog_id>/latest/<int:latest_id>/edit',
           methods=['GET', 'POST'])
def editLatestItem(catalog_id, latest_id):
    editedItem = session.query(LatestItem).filter_by(id=latest_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['price']:
            editedItem.price = request.form['price']
        session.add(editedItem)
        flash('Latest Item Successfully Edited')
        session.commit()
        return redirect(url_for('showList', catalog_id=catalog_id))
    else:

        return render_template(
            'editLatestitem.html', catalog_id=catalog_id, latest_id=latest_id, item=editedItem)

   
# Delete a latest item


@app.route('/catalog/<int:catalog_id>/latest/<int:latest_id>/delete',
           methods=['GET', 'POST'])
def deleteLatestItem(catalog_id, latest_id):
    itemToDelete = session.query(LatestItem).filter_by(id=latest_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        flash('Latest Item Successfully Deleted')
        session.commit()
        return redirect(url_for('showCatalogs', catalog_id=catalog_id))
    else:
        return render_template('deleteLatestItem.html', item=itemToDelete)
   

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)

