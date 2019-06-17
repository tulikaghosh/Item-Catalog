# Item Catalog

This application provides a list of items within a variety of categories as well as provide a user registration and authentication system.
Registered users will have the ability to post, edit and delete their own items.

## Features
Proper authentication and authorisation check.
Full CRUD support using SQLAlchemy and Flask.
JSON endpoints.
Implements oAuth using Google Sign-in API.

## Installation

* Download and install `Vagrant`.
* Download and install `VirtualBox`.
* Clone or download the Vagrant VM configuration file from https://github.com/udacity/fullstack-nanodegree-vm.git
* Open the above directory and navigate to the `vagrant`.
* Launch vagrant: `vagrant up`
* Connect to the newly created VM: `vagrant ssh`
* Change directory to /vagrant: `cd /vagrant`.
* Set up the database: `python database_setup.py`.
* Populate the database with some initial data: `python lotsofmenus.py`
* Launch application: `python finalproject.py`
* Open the browser and go to `http://localhost:8000`. 


##JSON endpoints
### Returns JSON of all catalogs
* '/catalog/JSON'
### Returns JSON of specific latest item
* '/catalog/<int:catalog_id>/latest/<int:latest_id>/JSON'
### Returns JSON of latest item
'/catalog/<int:catalog_id>/latest/JSON'
