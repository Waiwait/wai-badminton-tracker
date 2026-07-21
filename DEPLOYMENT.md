# DEPLOYMENT

To set this up, you'll need to set up a web service and a database which should take 5-10 minutes. I recommend deploying this on render (web-app)/ aiven(database) as they offer free hosting.

## Database (Aiven)

- Sign up/in via [Aiven](https://console.aiven.io/signup)
- Create a workspace if needed `Workspace (Top Bar) > + New Workspace > Hobby > Create Workspace`
- Create a project to store the database `Projects (Top Bar) > Create Project`
- From your new project, crea the database `Services (Left Bar) > Create Service > PostgreSQL`
- For the database configuration:

```
Service tier: Free
Cloud: (whatever region closest to your location)
Plan: Free-1-1gb
Name: (Give it a name)

```
and then `Create service`


## App Service (Render)

- Sign up/in via [Render](https://dashboard.render.com/register)
- Create a new web service pointing to the code repository `New Web Service > Public Git Repository > https://github.com/Waiwait/wai-badminton-tracker > Connect` (You can also fork this repository into your own GitHub account and deploy from there if you want full control over future changes.)
- For the configuration:

```
Name: (Give it a name, I recommend the name of your club)
Language: Docker
Region: (whatever region closest to the region you set up the database)
Instance Type: Free
Root Directory: (leave empty)


Environment Variables: Click Add from .env and copy and paste the following:


DATABASE_URL= >>> Copy this from Aiven > Services > DATABASE > Connection information > Service URI
DJANGO_ALLOWED_HOSTS=Leave blank for now, this is the URL that's generated for the instance by Render
DJANGO_DEBUG=False
DJANGO_SECRET_KEY= Generate this via https://djecrety.ir/
DJANGO_SUPERUSER_EMAIL= >>> This will be the admin account for you to log into
DJANGO_SUPERUSER_PASSWORD= >>> This will be the admin account for you to log into
DJANGO_SUPERUSER_USERNAME= >>> This will be the admin account for you to log into
PORT=10000

and then `Deploy Web Service`
```

## Post Deployment

Congratulations! After a few minutes, your application should be hosted on something like https://{your-app-name}.onrender.com/. This can be found on the Web Service page. Add this back to DJANGO_ALLOWED_HOST WITHOUT the https:// part (Manage > Environment > Update the variable > Save, rebuild and deploy )
To get started, login with the admin credentails you generated earlier, and generate a session to manage via Sessions. You can also import players via ebadders/superbadders as outlined [here](README.md#import-players)
Do note that because it's the free tier, if it's left inactive, the website will take 1-2 minutes to turn back on again. To work around this: once you've created a session, I recommend running a cron job via https://console.cron-job.org/ against a session summary every 14 minutes, this will keep the app/database from sleeping.
