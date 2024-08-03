
# PropScreen README

## PropScreen GitBook

Want to learn about how PropScreen works at a high level? Check out our [GitBook](https://propscreen.gitbook.io/propscreen)

## Containerization Locally and In "Production"

### Flask Env File
Before deployment you need to create a .flaskenv file with the following information

```sh
SECRET_KEY=your_secret_key
FLASK_APP=flask_for_startups.py
FLASK_DEBUG=1
FLASK_CONFIG=dev
DEV_DATABASE_URI=postgresql://postgres:postgres@db/postgres
TEST_DATABASE_URI=postgresql://postgres:postgres@db/postgres
REMEMBER_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
AWS_ACCESS_KEY_ID=YOUR_AWS_KEY
AWS_SECRET_ACCESS_KEY=YOUR_AWS_ACCESS_KEY
AWS_DEFAULT_REGION=YOUR_AWS_REGION
PGADMIN_DEFAULT_EMAIL=YOUR_DEFAULT_ADMIN_EMAIL
PGADMIN_DEFAULT_PASSWORD=YOUR_DEFAULT_ADMIN_PASSWORD
PGADMIN_DISABLE_POSTFIX=true
PGADMIN_LISTEN_ADDRESS=0.0.0.0
PGADMIN_LISTEN_PORT=3000
MASTER_PASSWORD_REQUIRED=False
CONTEXT_BUCKET=YOUR_AWS_S3_BUCKET_1
CONTEXT_OBJECT=YOUR_AWS_S3_CSV_FILE_1
ORG_SI_HASH_DB=YOUR_AWS_S3_BUCKET_2
HASHES_OBJECT=YOUR_AWS_S3_CSV_FILE_2
```

### Set up Credentials for PGAdmin

```sh
export PG_USER=postgres
```

```sh
echo "$(cat <<EOM
{
  "Servers": {
  "1": {
      "Name": "PropScreen_DB",
      "Group": "Server_Group_1",
      "Port": 5432,
      "Username": "$PG_USER",
      "Host": "db",
      "SSLMode": "prefer",
      "MaintenanceDB": "postgres"
    }
  }
}
EOM
)" > .pgadmin_servers.json
```

### Build and Launch the Containers

Locally:

Only starts the containers that make sense on the localhost, e.g. Caddy is skipped
because it won't be able to manage the SSL certificates for the production domain
from the NAT'd LAN anyway.

```sh
docker compose up app db pgadmin
```

If you've made changes to the source code that you need the be included in the
"app" container (the flask app) then you can do this (the extra --build flag)

```sh
docker compose up app db pgadmin --build
```

In "Production" (starts all 4 of the containers, including Caddy):
```sh
docker compose up -d
```

### If you need to wipe the database

```sh
docker compose down -v
```

## Acknowledgements
Nuvic's Flask For Startups, [link here](https://github.com/nuvic/flask_for_startups)\
pgAdmin, [link here](https://www.pgadmin.org/)\
caddy, [link here](https://caddyserver.com/)\
LLM Guard [link here](https://llm-guard.com/)