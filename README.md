[![Autodeployment dev](https://github.com/mithem/compolvo/actions/workflows/autodeployment.yml/badge.svg?branch=dev)](https://github.com/mithem/compolvo/actions/workflows/autodeployment.yml)

# compolvo

Tool for comparing and subscribing to different software services, and for managing the installation
and upgrade process on multiple devices.

## Run instructions

### Prerequisites

```bash
cd infrastructure
cp sample.env .env
```

Then, adjust the `.env` file to your needs (especially set the `STRIPE_API_KEY` to the key
provided.)

### Docker

From `infrastructure`, run:

```bash
docker compose up -d --build mariadb frontend server reverse-proxy
```

After the containers are running, you can access the frontend at http://localhost:8080.

For detailed usage instructions, check out the [User Guide](documentation/user_guide.md).

### User Credentials

By default, the following users are created for demonstration purposes:

| E-Mail            | Password   | Role  |
|-------------------|------------|-------|
| test@example.com  | Test12345! | User  |
| admin@example.com | admin      | ADMIN |