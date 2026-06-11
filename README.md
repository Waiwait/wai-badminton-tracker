# Badminton Matchmaking Web App

This is a web application designed to handle badminton matchmaking.  
It is built using **HTML**, **Django**, and **HTMX**.

---

# Getting Started

This project requires **Docker** to run. Docker is used as a containerisation service that installs and manages all required dependencies automatically.

---

## First-Time Setup

Copy the example environment `.env.example` file -> `.env`
Generate a Django secret key using:
https://djecrety.ir
Add the generated `DJANGO_SECRET_KEY` to your `.env` file.

Add details for the admin account in the `.env` file.  
These will be used to automatically create a superuser on server startup.

---

## Running the Project

Start the application using Docker Compose:

 `docker compose up`

 Note: The first run may require a second attempt as the database may not be fully ready on initial startup.

 This command will:

- Apply migrations
- Install requirements
- Start the Django development server
- Create the superuser (if configured)

---

## Static Files

Static files are automatically generated on container startup via the `docker-entrypoint`.  
In the future, this should be handled via a Git hook.

---

## Create migrations

If making changes to any models, make/run migrations via
`docker exec -it wai-badminton-tracker-web-1 python manage.py makemigrations core`
`docker exec -it wai-badminton-tracker-web-1 python manage.py migrate`
Container startup will also automatically apply any existing migrations via the `docker-entrypoint`.

--

## Getting up and running

- Login to the admin panel via `http://localhost:8000/`
- From the admin panel -> create a session, access via link
- Load data (from superbadders) via `http://localhost:8000/import-players/`



