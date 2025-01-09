# Typosquatting Detection and Scheduler App

This project is a **Typosquatting Detection System** combined with a **scheduled scanning service**. It includes a **Flask web application** for managing domains and viewing scan results, along with a **background scheduler** for automated periodic scanning.

---

##  **System Requirements**

- **Python 3.8+**
- **Anaconda** (optional but recommended)
- **Virtual Environment** (`venv` or `conda`)

---

##  **Installation**

1. **Clone the repository:**

git clone https://gitlab-stud.elka.pw.edu.pl/kwolanin/typoscanning.git



2. **Create and activate a virtual environment**


3. **Install dependencies:**


pip install -r requirements.txt


4. **Add your access data at .env:**


    VIRUSTOTAL_API_KEY=YOUR_API_KEY    #get from https://www.virustotal.com/
    MAIL_PASSWORD=YOUR_EMAIL_PASSWD
    SECRET_KEY=YOUR_SECRET_KEY         


5. **Initialize the database:**

python app.py

The app will automatically create the SQLite database.

---

##  **Running the Application**

The application and scheduler can be started together using a single script.

**Run the application and scheduler:**
python run.py


**Run only the Flask app:**
python app.py


**Run only the scheduler:**
python scheduler_runner.py

---

##  **Access the Application**

Open your browser and navigate to:
http://127.0.0.1:5000/


---

##  **Features**

### **Flask Application:**
- **Domain Management:** Add, edit, and delete domains.
- **Scan History Overview:** Track previous scans and their results.
- **Scheduler Configuration:** Set up daily, weekly, monthly, or custom CRON-based scanning schedules.

### **Scheduler:**
- **Automated Scanning:** Scheduled domain scanning based on CRON expressions.
- **Email Notifications:** Receive PDF and TXT attachments summarizing alerts.
- **Custom CRON Expressions:** Set flexible schedules for specific needs.

### **Report Formats:**
- **PDF Report:** Detailed report with tables of alerted domains.
- **TXT Report:** Simple list of alerted domains ready for firewall integration.

---

##  **CRON Scheduler Configuration**

You can configure various scan intervals:
- **Daily at 7:00 AM:** `0 7 * * *`
- **Weekly on Monday at 7:00 AM:** `0 7 * * 1`
- **Monthly:** `0 7 1 * *`
- **Custom CRON Expression:** Example: `*/5 * * * *` (every 5 minutes)

---

## **Email Configuration**

Email settings are located in **`app.py`**:


    app.config['MAIL_SERVER'] = 'smtp.example.com' 
    app.config['MAIL_PORT'] = 587 
    app.config['MAIL_USERNAME'] = 'your_email@example.com'

---



##  **Example TXT Report**

When an email is sent, it includes a TXT attachment like this:

    Alerted Domains Report for user@example.com Generated on: 2025-01-08 22:00:00
    
    Domain: example.com Scan Date: 2025-01-08 21:05:28
    alert1.com 
    alert2.com



This file can be directly used for your firewall/proxy configuration.

---


**Thank you for using the TypoScanning App!**