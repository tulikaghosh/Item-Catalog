#!/usr/bin/env python

from flask import Flask, render_template, request, redirect
from flask import jsonify, url_for, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Catalog, LatestItem, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog"

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
    return render_template('login.html', STATE=state)


# Validation and authorization
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;\
border-radius: 150px;-webkit-border-radius: 150px;\
-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps
                                 ('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
        % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps(
                'Failed to revoke token for given user.',
                400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs for Catalog information
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
def catalogsJSON():
    catalogs = session.query(Catalog).all()
    return jsonify(calalogs=[r.serialize for r in calalogs])

    # Show all catalog


@app.route('/')
@app.route('/catalog/')
def showCatalogs():
    catalogs = session.query(Catalog).all()
    # return "This page will show all catalogs"
	if 'username' not in login_session:
        return render_template('publiccatalog.html', catalogs=catalogs)
    else:
        return render_template('catalog1.html', catalogs=catalogs)

# Create a new catalog
@app.route('/catalog/new/', methods=['GET', 'POST'])
def newCatalog():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCatalog = Catalog(name=request.form['name'],
		   user_id=login_session['user_id'])
        session.add(newCatalog)
        flash('New Catalog %s Successfully Created' % newCatalog.name)

        session.commit()
        return redirect(url_for('showCatalogs'))
    else:
        return render_template('newCatalog1.html')
    # return "This page will be for making a new catalog"

# Edit a catalog


@app.route('/catalog/<int:catalog_id>/edit/', methods=['GET', 'POST'])
def editCatalog(catalog_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedCatalog = session.query(
        Catalog).filter_by(id=catalog_id).one()
	if editedCatalog.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this catalog. Please create your own catalog in order to edit.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['name']:
            editedCatalog.name = request.form['name']
            flash('Catalog Successfully Edited %s' % editedCatalog.name)

            return redirect(url_for('showCatalogs'))
    else:
        return render_template(
            'editCatalog1.html', catalog=editedCatalog)

    # return 'This page will be for editing catalog %s' % catalog_id


# Delete a catalog

@app.route('/catalog/<int:catalog_id>/delete/', methods=['GET', 'POST'])
def deleteCatalog(catalog_id):
    if 'username' not in login_session:
        return redirect('/login')
    catalogToDelete = session.query(
        Catalog).filter_by(id=catalog_id).one()
	if catalogToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this catalog. Please create your own catalog in order to delete.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(catalogToDelete)
        flash('Successfully Deleted')
        session.commit()
        return redirect(
            url_for('showCatalogs', catalog_id=catalog_id))
    else:
        return render_template(
            'deleteCatalog1.html', catalog=catalogToDelete)
    # return 'This page will be for deleting catalog %s' % catalog_id

# Show a calalog list
@app.route('/catalog/<int:catalog_id>/')
@app.route('/catalog/<int:catalog_id>/list/')
def showList(catalog_id):
    catalog = session.query(Catalog).filter_by(id=catalog_id).one()
    items = session.query(LatestItem).filter_by(
	    catalog_id=catalog_id).all()
	 if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publiclist.html', items=items, catalog=catalog)
    else:	
        return render_template('list1.html', items=items, catalog=catalog)

# Create a new latest item
@app.route(
    '/catalog/<int:catalog_id>/list/new/', methods=['GET', 'POST'])
def newLatestItem(catalog_id):
    if 'username' not in login_session:
        return redirect('/login')
    catalog = session.query(Catalog).filter_by(id=catalog_id).one()
	if login_session['user_id'] != catalog.user_id:
        return "<script>function myFunction() {alert('You are not authorized to add items to this catalog. Please create your own catalog in order to add items.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        newItem = latestItem(
            name=request.form['name'],
            description=request.form['description'],
            price=request.form['price'],
            catalog_id=catalog_id,
			user_id=catalog.user_id)
        session.add(newItem)
        flash('New list %s Item Successfully Created' % (newItem.name))
        session.commit()

        return redirect(url_for('showList', catalog_id=catalog_id))
    else:
        return render_template('newlatestitem1.html', catalog_id=catalog_id)

# Edit a latest item
@app.route('/catalog/<int:catalog_id>/latest/<int:latest_id>/edit',
           methods=['GET', 'POST'])
def editLatestItem(catalog_id, latest_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(LatestItem).filter_by(id=latest_id).one()
	if login_session['user_id'] != catalog.user_id:
        return "<script>function myFunction() {alert('You are not authorized to edit items to this catalog. Please create your own catalog in order to edit items.');}</script><body onload='myFunction()'>
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
            'editLatestitem1.html', catalog_id=catalog_id,
            latest_id=latest_id, item=editedItem)


# Delete a latest item

@app.route('/catalog/<int:catalog_id>/latest/<int:latest_id>/delete',
           methods=['GET', 'POST'])
def deleteLatestItem(catalog_id, latest_id):
    if 'username' not in login_session:
        return redirect('/login')
    itemToDelete = session.query(LatestItem).filter_by(id=latest_id).one()
	if login_session['user_id'] != catalog.user_id:
        return "<script>function myFunction() {alert('You are not authorized to delete menu items to this catalog. Please create your own catalog in order to delete items.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(itemToDelete)
        flash('Latest Item Successfully Deleted')
        session.commit()
        return redirect(url_for('showCatalogs', catalog_id=catalog_id))
    else:
        return render_template('deleteLatestItem1.html', item=itemToDelete)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
