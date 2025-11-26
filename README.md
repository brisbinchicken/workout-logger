# Workout Logger

A modern, self-hosted, mobile-friendly workout tracking application built with Flask and Tailwind CSS. Designed to be simple, fast, and aesthetically pleasing.

[Workout Logger Desktop Screenshot](https://imgur.com/a/odMRIYs)

[Workout Logger Mobile Screenshot](https://imgur.com/a/mTwKoZG)

## Features

*   **📱 Mobile & Desktop Friendly:** A fully responsive GUI that adapts to any screen size. Large, easy-to-tap buttons for logging sets on the go.
*   **Log Workouts:** Quickly log exercises, sets, reps, weight, and notes.
*   **History Tracking:** View a detailed history of past workouts with date filtering.
*   **Excel Export:** "Finish" your workout to automatically generate and save an Excel (`.xlsx`) report.
*   **Admin Dashboard:** Manage exercises (add/disable) and update security settings.
*   **Dark/Light Mode:** Beautiful UI with automatic or manual theme switching.
*   **Dockerised:** Ready for easy deployment with Docker Compose.
*   **NAS/SMB Integration:** Automatically save workout exports and backups to a local folder or network share.

## Tech Stack

*   **Backend:** Python (Flask), SQLite, SQLAlchemy
*   **Frontend:** HTML5, Tailwind CSS (via CDN), JavaScript
*   **Authentication:** Flask-Login, Bcrypt
*   **Data Export:** OpenPyXL
*   **Containerisation:** Docker, Docker Compose

---

## ⚙️ Configuration Guide (Read First!)

Before running the app, you must configure the `.env` file. This file tells the application where to save your data, what timezone to use, and how to secure your session.

### 1. Create the Configuration File
Copy the example file to create your production configuration:
```bash
cp .env.example .env
```

### 2. Edit `.env`
Open `.env` in any text editor and adjust the following settings to match your environment:

#### 🔐 Security
*   `FLASK_SECRET_KEY`: **Required.** Change this to a long, random string. This encrypts your session cookies to keep you logged in securely.
*   `ADMIN_USERNAME`: The username you will use to log in (default: `admin`).
*   `ADMIN_PASSWORD_HASH`: (Optional) You can leave this blank.
    *   *If blank:* The app creates the user with **no password** on the first run. You must log in and set a password immediately in the Admin dashboard.
    *   *If set:* You can generate a bcrypt hash online or via python and paste it here to pre-set a password.

#### 🌍 Localisation
*   `TIMEZONE`: **Critical.** Set this to your local timezone (e.g., `America/New_York`, `Australia/Brisbane`, `Europe/London`).
    *   *Why?* This ensures your workouts are logged on the correct day and time. If incorrect, your logs might appear on the wrong date.

#### 💾 Storage & NAS Setup
The app saves data in two places: internal Docker volumes (for the app to work) and an external "Host Path" (for you to access your files).

*   `SMB_MOUNT_HOST_PATH`: This is the folder **on your computer/server** where you want Excel exports and Backups to appear.
    *   **Local Folder:** If you just want files on your server, set this to a path like `./my_workout_data`.
    *   **NAS (Network Storage):** To save to a NAS (Synology, Unraid, TrueNAS), you must **first mount the NAS share to your host machine** (e.g., mount `//192.168.1.10/backups` to `/mnt/nas`). Then, set this variable to `/mnt/nas`.
*   `EXPORTS_SUBDIR`: Name of the folder for Excel files (default: `exports`).
*   `BACKUPS_SUBDIR`: Name of the folder for Database backups (default: `backups`).

---

## 🚀 Installation

### Prerequisites
*   Docker and Docker Compose installed on your machine.

### Steps

1.  **Clone the repository** (or download the files):
    ```bash
    git clone https://github.com/brisbinchicken/workout-logger.git
    cd workout-logger
    ```

2.  **Configure your `.env` file** (see guide above).

3.  **Run with Docker**:
    This command downloads dependencies and starts the server.
    ```bash
    docker-compose up -d --build
    ```

4.  **Access the App**:
    Open your browser and navigate to `http://localhost:8080` (or the IP address of your server).

### Initial Setup
1.  **Login**: Use the `ADMIN_USERNAME` you set (default: `admin`).
2.  **Set Password**: Go to the **Admin** page immediately to set your secure password.
3.  **Add Exercises**: The app comes with a default list. Use the Admin page to add custom exercises or disable ones you don't use.

---

## 📂 Data & Backups Explained

### Where is my data?
*   **Database (`workouts.sqlite`)**: Stored securely inside the Docker volume `db_data`. It persists even if you restart or delete the container.
*   **Excel Exports**: When you click "Finish" on a workout, an Excel file is created in your `SMB_MOUNT_HOST_PATH`/`exports` folder.

### Automatic Backups (Cron)
The container runs a background scheduler (cron) to keep your data safe:
*   **Daily Database Backup**: Runs every night at **02:10 AM**. Copies the database to your `SMB_MOUNT_HOST_PATH`/`backups` folder.
*   **Weekly Summary**: Runs every **Sunday at 02:00 AM**. Generates a weekly Excel summary.
*   **Retention Policy**: The system automatically keeps the last **14 backups** and deletes older ones to prevent filling up your storage.

---

## Usage Tips
*   **Logging**: Select an exercise, enter details, and click "Log Set".
*   **Finishing**: When done, click "Finish" on the main page. This "locks" the day and generates the Excel report.
*   **Resetting**: If you made a mistake, use the "Reset" button (only available before finishing) to wipe the current day's logs.

## License
[MIT License](LICENSE)


