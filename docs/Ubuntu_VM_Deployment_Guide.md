# FastAPI Ubuntu VM Deployment Guide (with PostgreSQL)

This guide walks you through deploying your FastAPI `project-3-todos` application to your new Hostinger Ubuntu VM and connecting it to the PostgreSQL database you created.

---

## Step 1: Prepare Your Code for Production

Right now, your database connection string in `todoapp/database.py` is hardcoded. You need to make it configurable via Environment Variables so your production VM can connect to the correct database (with the `prince` user).

Modify `todoapp/database.py` to read from an environment variable, falling back to localhost for your Mac development:

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Use the OS environment variable if it exists, otherwise fall back to the old string
SQLALCHEMY_DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql://postgres:test1234@localhost/TodoApplicationDatabase"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
```

## Step 2: Transfer Your Code to the VM

The easiest way to get your code onto the VM is using Git.
1. Push your code to a GitHub repository from your Mac.
2. SSH into your VM:
   ```bash
   ssh root@<your_vm_ip>
   ```
3. Install `git` and clone your repository (it's best to put it in `/var/www/` or your home directory `~`):
   ```bash
   sudo apt update
   sudo apt install git
   cd ~
   git clone <your_repo_url>
   cd project-3-todos   # Navigate into the project folder
   ```

*(Alternative: You can use `scp` or `rsync` from your Mac terminal to copy the folder directly if you don't want to use GitHub.)*

## Step 3: Set Up the Python Environment on the VM

You need to install Python, pip, a virtual environment, and your dependencies on the Ubuntu server.

```bash
# Install Python tools
sudo apt install python3-pip python3-venv

# Create a virtual environment inside your project folder
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install your project requirements
# Note: Since you use `uv`, you can install uv first:
pip install uv
uv sync # Or pip install -r requirements.txt if you generated one
```

## Step 4: Configure Your Environment Variable

Now that your code reads `DATABASE_URL`, we need to set this variable on the server. There are multiple ways to do this, but since we will run FastAPI via `systemd` (in Step 5), we will create a `.env` file that the systemd service can load.

Create a file named `.env` in the root of your project on the VM:
```bash
nano /home/yourusername/project-3-todos/.env
```
Add the following line (replace `<your_db_password>` with the password you set for the `prince` super user):
```env
DATABASE_URL=postgresql://prince:<your_db_password>@localhost/TodoApplicationDatabase
```
Save and exit (`CTRL+X`, `Y`, `Enter`).

## Step 5: Run FastAPI as a Background Service (Systemd)

You don't want FastAPI to stop when you close your SSH terminal. We will use `systemd` to run Uvicorn as a background service that automatically restarts if the server reboots.

1. Create a systemd service file:
   ```bash
   sudo nano /etc/systemd/system/todoapp.service
   ```
2. Paste the following configuration. **Make sure to change `yourusername` to the actual user folder where you cloned the project (e.g., `root` or `prince`)**:
   ```ini
   [Unit]
   Description=Gunicorn instance to serve FastAPI Todo Application
   After=network.target

   [Service]
   User=root
   Group=www-data
   WorkingDirectory=/root/project-3-todos/todoapp
   # Load the environment variables
   EnvironmentFile=/root/project-3-todos/.env
   # Path to uvicorn inside your virtual environment
   ExecStart=/root/project-3-todos/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
   *(Note: Adjust the WorkingDirectory and ExecStart paths if you cloned the repo somewhere else)*

3. Start and enable the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start todoapp
   sudo systemctl enable todoapp
   ```
4. Check the status to make sure it's running cleanly:
   ```bash
   sudo systemctl status todoapp
   ```

## Step 6: Configure Nginx as a Reverse Proxy

FastAPI is now running locally on the VM at port 8000 (`http://127.0.0.1:8000`). We need to expose this to the internet via port 80 (standard HTTP) using Nginx.

1. Install Nginx:
   ```bash
   sudo apt install nginx
   ```
2. Create an Nginx server block configuration for your app:
   ```bash
   sudo nano /etc/nginx/sites-available/todoapp
   ```
3. Paste the following configuration (replace `your_vm_ip` with your Hostinger VM's public IP address or your domain name):
   ```nginx
   server {
       listen 80;
       server_name <your_vm_ip>;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
4. Enable the configuration by linking it to `sites-enabled`:
   ```bash
   sudo ln -s /etc/nginx/sites-available/todoapp /etc/nginx/sites-enabled/
   ```
5. Remove the default Nginx page:
   ```bash
   sudo rm /etc/nginx/sites-enabled/default
   ```
6. Test your Nginx configuration for syntax errors:
   ```bash
   sudo nginx -t
   ```
7. Restart Nginx to apply changes:
   ```bash
   sudo systemctl restart nginx
   ```

## Conclusion

Your FastAPI application should now be live at `http://<your_vm_ip>`. It securely runs locally on port 8000, proxied via Nginx to the internet on port 80, and is safely connected to the `TodoApplicationDatabase` PostgreSQL using the `prince` super user credentials.

If you hit any endpoints or navigate to `http://<your_vm_ip>/docs`, you will see your Swagger UI powered by the production database.
