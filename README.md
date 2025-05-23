# Python Flask Blog

A monolithic blog application built with Python, Flask, and SQLite, featuring token-based authentication for the admin.

## Features

- Admin authentication (JWT-based)
- CRUD operations for posts (Admin only)
- Markdown support for post content
- Image uploads
- Video embedding (via URL)
- Code block syntax highlighting (Prism.js)
- Code block copy-to-clipboard
- Public view for posts (list and detail)
- Pagination

## Setup

1.  **Clone the repository (if applicable) or create the files as provided.**

2.  **Create a virtual environment and activate it:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create a `.env` file** in the root directory and add a `SECRET_KEY`:
    ```
    SECRET_KEY='your_very_secret_random_string_here'
    # Optional: DATABASE_URL='sqlite:///path/to/your/database.sqlite'
    ```

5.  **Initialize the database:**
    Flask-Migrate is used for database migrations.
    ```bash
    flask db init  # Run only once to initialize migrations
    flask db migrate -m "Initial migration with User and Post tables"
    flask db upgrade
    ```

6.  **Create an initial admin user:**
    Open the Flask shell:
    ```bash
    flask shell
    ```
    Then run the following Python commands:
    ```python
    from app import db
    from app.models import User
    # Check if admin user exists
    if User.query.filter_by(username='admin').first() is None:
        admin = User(username='admin')
        admin.set_password('your_secure_password') # Change this password!
        db.session.add(admin)
        db.session.commit()
        print('Admin user created.')
    else:
        print('Admin user already exists.')
    exit()
    ```

7.  **Download Prism.js for Syntax Highlighting:**
    -   Go to [Prism.js Download Page](https://prismjs.com/download.html).
    -   Select your desired themes and languages.
    -   Download `prism.js` and `prism.css`.
    -   Place `prism.js` into `app/static/js/`.
    -   Place `prism.css` into `app/static/css/`.

8.  **Run the application:**
    ```bash
    flask run
    # or python run.py
    ```
    The blog will be accessible at `http://127.0.0.1:5000/`.
    Admin login is at `http://127.0.0.1:5000/login`.

## Project Structure

(Refer to the structure provided in the development steps.)

