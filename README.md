
## Project Description

This project is the backend API for Coderr, a service marketplace platform. It's built using Django REST Framework and provides API endpoints for user registration, login, profile management, offer creation, order management, reviews, and more.
The Backend is a part of the frontend project [coderr](https://github.com/Developer-Akademie-Backendkurs/project.Coderr), which you have to download.

## Installation

Follow these steps to set up and run the `coderr_backend` project locally:

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/jurin1/coderr_backend
    cd coderr_backend
    ```
    
2.  **Create a virtual environment (Recommended):**

    It's best practice to create a virtual environment to isolate project dependencies.

    ```bash
    # For Linux/macOS
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    venv\Scripts\activate
    ```

3.  **Install Dependencies:**

    Install the required Python packages listed in `requirements.txt`.

    ```bash
    pip install -r requirements.txt
    ```

4.  **Apply Database Migrations:**

    This project uses Django migrations to manage the database schema. Apply the migrations to create the database tables.

    ```bash
    python manage.py migrate
    ```

5.  **Create a Superuser (Optional):**

    If you want to access the Django admin panel, you'll need to create a superuser account.

    ```bash
    python manage.py createsuperuser
    ```
    Follow the prompts to enter a username, email, and password for the superuser.

6.  **Run the Development Server:**

    Start the Django development server to run the backend application.

    ```bash
    python manage.py runserver
    ```

    The server will start at `http://127.0.0.1:8000/` or `http://localhost:8000/`.

## Usage

*   **Access the API:** The API endpoints are available under the `/api/` path. For example, user registration endpoint is at `http://127.0.0.1:8000/api/registration/`. Refer to the `coderr_app/urls.py` file for a complete list of API endpoints.

*   **Django Admin Panel:**  If you created a superuser, you can access the Django admin panel at `http://127.0.0.1:8000/admin/`. Log in with your superuser credentials to manage the backend data.

*   **Testing:** You can run tests using the Django test runner:

    ```bash
    python manage.py test coderr_app
    ```


## Git Commit Script (`git_commit.py`)

The `git_commit.py` script is a helper script to automate the process of adding changes, committing them with a message, and pushing to the remote repository.

To use it, run:

```bash
python git_commit.py "Your commit message here"
