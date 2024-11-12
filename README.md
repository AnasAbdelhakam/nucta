
# Step-by-Step Installation Guide for Setting up Frappe, ERPNext, and Custom App (Nucta)

This guide will walk you through setting up Frappe, ERPNext, and your custom app, Nucta. Follow each step carefully to ensure a successful installation.

## Prerequisites

Make sure your server meets the following requirements:
- **Operating System:** Ubuntu 20.04 or 22.04
- **RAM:** Minimum 4GB (8GB recommended)
- **User Privileges:** A non-root user with sudo privileges

---

## Step 1: Install Frappe

Follow these steps to install the Frappe framework:

### 1. Install Dependencies

```bash
sudo apt update
sudo apt install python3-dev python3-pip mariadb-server redis-server curl nginx
sudo apt install software-properties-common
```

### 2. Setup MariaDB

Configure MariaDB for Frappe. Update your MariaDB configuration to be compatible with Frappe:

```bash
sudo mysql_secure_installation
sudo nano /etc/mysql/mariadb.conf.d/50-server.cnf
```

Add or modify the following lines under the `[mysqld]` section:

```ini
[mysqld]
innodb-file-format=barracuda
innodb-file-per-table=1
innodb-large-prefix=1
character-set-client-handshake = FALSE
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
```

Restart MariaDB:

```bash
sudo systemctl restart mariadb
```

### 3. Install Node.js and Redis

```bash
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt install -y nodejs
```

### 4. Install Yarn

```bash
sudo npm install -g yarn
```

### 5. Install Bench

Bench is a command-line tool to manage Frappe deployments:

```bash
sudo pip3 install frappe-bench
bench init --frappe-branch version-14 frappe-bench
cd frappe-bench
```

### 6. Create a New Site

Create a new Frappe site:

```bash
bench new-site yoursite.com
```

---

## Step 2: Install ERPNext

### 1. Add ERPNext App

Navigate to your Frappe bench directory and get the ERPNext app:

```bash
bench get-app --branch version-14 erpnext
```

### 2. Install ERPNext on Your Site

Install ERPNext on the site you created earlier:

```bash
bench --site yoursite.com install-app erpnext
```

### 3. Start the Bench

To verify everything is working properly:

```bash
bench start
```

---

## Step 3: Install Custom App (Nucta)

### 1. Clone the Nucta App

Download your custom app from GitHub:

```bash
wget https://github.com/ztechnium/nucta/archive/refs/heads/main.zip -O nucta-main.zip
unzip nucta-main.zip
```

### 2. Install Nucta on Your Site

Install the Nucta app on your Frappe site:

```bash
bench --site yoursite.com install-app nucta
```

---

## Step 4: Configure Nucta Settings

### 1. Access the Nucta Settings

Log in to your ERPNext/Frappe instance and navigate to Nucta Settings from the sidebar menu.

### 2. Make Basic Edits

Fill in the necessary details for the basic settings of Nucta, such as default configurations, etc., and save your changes.

---

## Final Steps

### Run Bench in Production Mode (Optional)

If you are ready to run in production:

```bash
sudo bench setup production yoursite.com
```

### Access ERPNext

You can access your ERPNext instance by navigating to `http://yoursite.com` in a web browser.

---

## References

- [Frappe Installation Documentation](https://frappe.io/docs)
- [ERPNext Installation Documentation](https://erpnext.com/docs)

For further customization or additional support with the installation, feel free to contact our support team.

---
