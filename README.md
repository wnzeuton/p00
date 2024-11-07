# p00 - bxlobog by lobo
## Roster
-  Will Nzeuton (Project Manager)
    - User Authentication
    - Creating Blog Entries
    - Built Database
    - Final Testing and Bug Fixes
- Daniel Park
  - Setup Flask and SQLITE3 Environment
  - Creating and Deleting Blogs
  - Built Database
  - Final Testing and Bug Fixes
- Tim Ng
  - Post Editing and Deleting
  - Performed majority of housekeeping (README.md, etc)
- YinWei Zhang
  - Organized file and middleware structure
  - Creating Blogs
  - Frontend (HTML and CSS)

## Description
This project is a web app that we built using Python and SQLite to allow users to create and view blog posts. When starting the app, you will be brought to the home page in which you have three options: logging in, creating an account, and viewing the blog page as a guest. In order to create or edit said post, you must have and be logged in to your account. Each blog has its own respective category, title, and creator listed to allow for greater sortability. We already have one blog post created by our lord and savior PM Nzeuton to show off our code. 

**Stats for nerds:**

Front End:

- Home Page: Option to register, login, or view blogs

- Signup/Login Pages: Fill in information for new or existing users 

- Blog Editor: Page to create/edit/delete posts 

Back End:

- Flask Server: Renders the webpages, request handling

- SQLite Database: Storage of user info, blog data, connections between user info and blog data

## Install Guide
Hey fellow Devos!

- Step 0: Go tell your ducky you love them

- Step 1: Locate the SSH clone link by finding the "Code" drop-down button towards the middle top of the page

- Step 2: Use 'git clone {link}' in the terminal. In this case the link is: ```git@github.com:wnzeuton/p00.git```

- Step 3: Install the required packages by running ```pip3 install -r requirements.txt``` in the terminal. Consider activating a virtual environment and installing the libraries there.

## Launch code

First, set up the database by running the following commands in the terminal:
```
python3 setup_db.py
```

Then, ensure you are in the parent folder (e.g., ../p00/) NOT (../p00/app/) and run the app:

```
flask run
```

Note: To turn on debug mode you can add a ```--debug``` tag after ```flask run```

