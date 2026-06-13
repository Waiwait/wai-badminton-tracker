# Wai-Badminton-Tracker

This is a lightweight web application designed to manage badminton sessions. Admin create sessions/users via the admin panel and then manage specific sessions via a central dashboard.

It is built using **HTML**, **Django**, and **HTMX**.

Licensed under the **PolyForm Noncommercial License 1.0.0**.  
See [LICENSE](LICENSE) for details.

**This software is for non-commercial use only.**

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


## Deploying

- Currently this is running on render (web-app) and aiven (postgres), the free tier being sufficient
- To deploy a version of this, I recommend to clone a copy of this repo and point render to your cloned project


