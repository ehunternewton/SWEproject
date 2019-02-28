#### This is to get familiar with the application structure, does not have to be the base build, but I suggest we build from it once we agree on models, classes and views since it has the login system

##### Feel free to update as you wish on local dev environment. We can work out the merges that go into master when approved

######Here Luis:
I suggest everybody make a dev git branch, I will do as well to avoid directly making changes on master

So far I modified the original code to make login work without confirmation email and added the ability to add roles.

Each one of us should be able to deploy this in pycharm or visual studio. 


Pre-Installation Steps: Install Python3!

INSTALLATION / RUN Instructions

1- after downloading the files run this command in terminal/DOS/Shell to create a virtual environment, make sure you are in xmenacademy folder:

`$ python3 -m venv venv` mac (I think is the same in windows)

2- Install flask and Activate the virtual environment

`$ source venv/bin/activate` mac
 
`$ venv\Scripts\activate` windows

3- There is a requirements.txt file in the project folder... your ide should ask you to download the dependencies... and you should. Make sure you are on version 3.
`$ pip install -r requirements.txt`

4- The next step is to initialize the local database. I believe that python 3 has sqlite by default. If not figure out how to install. Perform the following commands in your terminal:

`$ flask shell`

The following statements initiate db because of sqlalchemy and model file:

`>>> from xmenacademy import db`
`>>> db.create_all()`

INSERT ROWS:

`>>> admin_role = Role(name='Admin')`

`>>> student_role = Role(name='Student')`

`>>> teacher_role = Role(name='Teacher')`

`>>> db.session.add(admin_role)`

`>>> db.session.add(student_role)`

`>>> db.session.add(teacher_role)`

COMMIT:

`>>> db.session.commit()`

5 - Run to see if it works. Enjoy!


Lets use this base code to create our models, routes and views for the rest of the requirements







XMEN ACADEMY
======

