import os
from flask import Flask, request, render_template, redirect, url_for, flash, make_response
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Domain, ScanHistory, ScanSettings, ScanDetails, Whitelist
from forms import LoginForm, RegisterForm, ScanSettingsForm, AlertForm
from scanner import quick_scan_domain, full_scan_domain
from flask_mail import Mail
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Init
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'typosquattingtest'
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = 'typosquattingtest@gmail.com'
mail = Mail(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.template_filter('format_datetime')
def format_datetime(value):
    if value:
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return "---"


# App Routes

@app.route("/", methods=["GET", "POST"])
def index():
    domain_input = ""

    if request.method == "POST":
        domain_input = request.form.get("domains", "").strip()
        if not domain_input:
            flash("Please enter a domain to analyze.", "danger")
            return render_template("index.html", results=[], found=0, total_permutations=0, domain_input=domain_input)

        try:
            # Quick Scan (save_to_db=False)
            scan_results = quick_scan_domain(domain_input)
            print("[DEBUG] Quick Scan Results:", scan_results)

            return render_template(
                "index.html",
                results=scan_results.get("domains", []),
                found=len(scan_results.get("valid_domains", [])),
                total_permutations=len(scan_results.get("generated_domains", [])),
                domain_input=domain_input
            )

        except Exception as e:
            flash(f"An error occurred during the scan: {e}", "danger")
            print("[ERROR]", e)
            return render_template("index.html", results=[], found=0, total_permutations=0, domain_input=domain_input)

    return render_template("index.html", results=[], found=0, total_permutations=0, domain_input=domain_input)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for('my_domains'))
        else:
            flash("Login unsuccessful. Please check your email and password.", "danger")
    return render_template('login.html', form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash("Your account has been created! You can now log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html", form=form)


@app.route("/my-domains", methods=["GET", "POST"])
@login_required
def my_domains():
    if request.method == "POST":
        new_domain = request.form.get("domain_name")
        if new_domain:
            domain = Domain(name=new_domain, owner=current_user)
            db.session.add(domain)
            db.session.commit()
        return redirect(url_for("my_domains"))

    domains = Domain.query.filter_by(user_id=current_user.id).all()
    for domain in domains:
        latest_scan = ScanHistory.query.filter_by(domain_id=domain.id).order_by(ScanHistory.date.desc()).first()
        if latest_scan:
            alerted_domains = json.loads(latest_scan.domains_alerted) if latest_scan.domains_alerted else []
            if alerted_domains:
                domain.status = "Needs Attention"
                print(f"[DEBUG] Domain: {domain.name}  Status: Needs Attention (Alerted domains found)")
            else:
                domain.status = "Clean"
                print(f"[DEBUG] Domain: {domain.name}  Status: Clean (No alerted domains)")
            domain.last_scanned = latest_scan.date
        else:
            domain.status = "Unknown"
            domain.last_scanned = None
            print(f"[DEBUG] Domain: {domain.name} Status: Unknown (No scans found)")

    return render_template("my_domains.html", domains=domains)


@app.route("/delete-domain/<int:domain_id>", methods=["POST"])
@login_required
def delete_domain(domain_id):
    domain = Domain.query.get_or_404(domain_id)
    if domain.owner != current_user:
        flash("You are not authorized to delete this domain.", "danger")
        return redirect(url_for("my_domains"))

    try:
        ScanHistory.query.filter_by(domain_id=domain.id).delete()
        db.session.commit()

        db.session.delete(domain)
        db.session.commit()

        flash(f"Domain '{domain.name}' has been successfully deleted.", "success")
        print(f"[DEBUG] Domain {domain.name} was deleted.")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to delete domain: {e}", "danger")
        print(f"[ERROR] Failed to delete domain: {e}")

    return redirect(url_for("my_domains"))


@app.route("/run-scan/<int:domain_id>")
@login_required
def run_scan(domain_id):
    domain = Domain.query.get_or_404(domain_id)
    if domain.owner != current_user:
        flash("You are not authorized to scan this domain.", "danger")
        return redirect(url_for("my_domains"))

    try:
        domain.status = "in progress"
        db.session.commit()

        full_scan_domain(domain)

        latest_scan = ScanHistory.query.filter_by(domain_id=domain.id).order_by(ScanHistory.date.desc()).first()

        if latest_scan:
            domain.last_scanned = latest_scan.date

            if latest_scan.domains_alerted and json.loads(latest_scan.domains_alerted):
                domain.status = "Needs Attention"
            else:
                domain.status = "Clean"
        else:
            domain.status = "unknown"  # if there were no scans yet

        db.session.commit()
        flash(f"Scan completed for {domain.name}.", "success")

    except Exception as e:
        domain.status = "Needs Attention"
        db.session.commit()
        flash(f"An error occurred: {e}", "danger")

    return redirect(url_for("my_domains"))


@app.route("/alerts", methods=["GET", "POST"])
@login_required
def alerts():
    form = AlertForm()
    domains = Domain.query.filter_by(user_id=current_user.id).all()
    selected_domain_id = request.form.get("selected_domain")
    whitelisted_domains = []

    # Mail settings
    if form.validate_on_submit() and 'alert_email' in request.form:
        current_user.alert_email = form.alert_email.data
        db.session.commit()
        flash("Alert email updated successfully!", "success")
        return redirect(url_for("alerts"))

    # Whitelist settings
    if selected_domain_id:
        try:
            selected_domain = Domain.query.get(int(selected_domain_id))
            if selected_domain and selected_domain.owner == current_user:
                whitelisted_domains = Whitelist.query.filter_by(domain_id=selected_domain.id).all()
                print(f"[DEBUG] Whitelist for domain {selected_domain.name}: {len(whitelisted_domains)} entries")
            else:
                flash("Invalid domain selection.", "danger")
        except ValueError:
            flash("Invalid domain ID provided.", "danger")

    # Add to WL
    if request.method == "POST" and 'whitelist_domain' in request.form:
        domain_id = request.form.get("selected_domain")
        whitelisted_domain = request.form.get("whitelist_domain")
        if domain_id and whitelisted_domain:
            domain = Domain.query.get(int(domain_id))
            if domain and domain.owner == current_user:
                existing_entry = Whitelist.query.filter_by(domain_id=domain.id,
                                                           whitelisted_domain=whitelisted_domain).first()
                if existing_entry:
                    flash(f"The domain '{whitelisted_domain}' is already in the whitelist for '{domain.name}'.", "info")
                else:
                    new_entry = Whitelist(domain_id=domain.id, whitelisted_domain=whitelisted_domain)
                    db.session.add(new_entry)
                    db.session.commit()
                    flash(f"Domain '{whitelisted_domain}' added to whitelist for '{domain.name}'.", "success")
            else:
                flash("Invalid domain selected.", "danger")

    form.alert_email.data = current_user.alert_email

    return render_template(
        "alerts.html",
        domains=domains,
        selected_domain_id=selected_domain_id,
        whitelisted_domains=whitelisted_domains,
        form=form
    )


@app.route("/remove-from-whitelist/<int:entry_id>", methods=["POST"])
@login_required
def remove_from_whitelist(entry_id):
    entry = Whitelist.query.get_or_404(entry_id)
    if entry.domain.owner != current_user:
        flash("You are not authorized to remove this entry from the whitelist.", "danger")
        return redirect(url_for("alerts"))

    try:
        db.session.delete(entry)
        db.session.commit()
        flash(f"Domain '{entry.whitelisted_domain}' removed from the whitelist.", "success")
        print(f"[DEBUG] Whitelist entry {entry.whitelisted_domain} removed successfully.")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to remove domain from whitelist: {e}", "danger")
        print(f"[ERROR] Failed to remove whitelist entry: {e}")

    return redirect(url_for("alerts"))


@app.route("/scan-settings", methods=["GET", "POST"])
@login_required
def scan_settings():
    form = ScanSettingsForm()
    domains = Domain.query.filter_by(user_id=current_user.id).all()
    form.domain.choices = [(d.id, d.name) for d in domains]

    if form.validate_on_submit():
        setting = ScanSettings.query.filter_by(user_id=current_user.id, domain_id=form.domain.data).first()
        if setting:
            setting.frequency = form.frequency.data
            setting.custom_cron = form.custom_cron.data
        else:
            setting = ScanSettings(
                user_id=current_user.id,
                domain_id=form.domain.data,
                frequency=form.frequency.data,
                custom_cron=form.custom_cron.data
            )
            db.session.add(setting)

        db.session.commit()
        flash("Scan settings updated successfully!", "success")
        return redirect(url_for("scan_settings"))

    settings = ScanSettings.query.filter_by(user_id=current_user.id).all()
    return render_template("scan_settings.html", form=form, settings=settings)


@app.route("/domain-history/<int:domain_id>")
@login_required
def domain_history(domain_id):
    domain = Domain.query.get_or_404(domain_id)
    if domain.owner != current_user:
        flash("You are not authorized to view this domain.", "danger")
        return redirect(url_for("my_domains"))

    history = ScanHistory.query.filter_by(domain_id=domain.id).order_by(ScanHistory.date.desc()).all()
    print(f"[DEBUG] Loading scan history fot {domain.name}: {len(history)} records")

    for scan in history:
        try:
            scan.alerted_domains_parsed = json.loads(scan.domains_alerted) if scan.domains_alerted else []
            print(f"[DEBUG] Scan ID: {scan.id}, Alerted Domains: {scan.alerted_domains_parsed}")
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSONDecodeError: {e}")
            scan.alerted_domains_parsed = []

    return render_template(
        "domain_history.html",
        domain=domain,
        history=history
    )


@app.route("/download-report/<int:scan_id>")
@login_required
def download_report(scan_id):
    scan = ScanHistory.query.get_or_404(scan_id)
    if scan.domain.owner != current_user:
        flash("You are not authorized to access this report.", "danger")
        return redirect(url_for("my_domains"))

    details = ScanDetails.query.filter_by(scan_id=scan.id).all()
    alerted_domains = json.loads(scan.domains_alerted) if scan.domains_alerted else []

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle(f"Scan Report - {scan.domain.name}")

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(30, 750, f"Scan Report for {scan.domain.name}")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(30, 730, f"Scan Date: {scan.date.strftime('%Y-%m-%d %H:%M:%S')}")
    pdf.drawString(30, 715, f"Number of Permutations: {scan.permutations_checked}")
    pdf.drawString(30, 700, f"Number of Existing Domains: {scan.existing_domains}")
    pdf.drawString(30, 685, f"Number of Alerted Domains: {len(alerted_domains)}")

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(30, 660, "Alerted Domains:")
    pdf.setFont("Helvetica", 12)

    y = 640
    for domain in alerted_domains:
        if y < 50:
            pdf.showPage()
            y = 750
        pdf.drawString(50, y, f"- {domain}")
        y -= 15

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(30, y - 20, "Scan Details:")
    pdf.setFont("Helvetica", 12)
    y -= 40

    for detail in details:
        if y < 50:
            pdf.showPage()
            y = 750
        pdf.drawString(50, y, f"Domain: {detail.domain_name}")
        pdf.drawString(50, y - 15, f"IP Address: {detail.ip_address}")
        pdf.drawString(50, y - 30, f"WHOIS Registrar: {detail.whois_registrar}")
        pdf.drawString(50, y - 45, f"WHOIS Country: {detail.whois_country}")
        pdf.drawString(50, y - 60, f"Similarity Score: {detail.similarity_score}")
        pdf.drawString(50, y - 75, f"Reputation: {detail.reputation}")
        y -= 100

    pdf.save()
    buffer.seek(0)

    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=report_{scan.id}.pdf'
    return response


@app.route("/scan-view/<int:scan_id>")
@login_required
def scan_view(scan_id):
    scan = ScanHistory.query.get_or_404(scan_id)
    if scan.domain.owner != current_user:
        flash("You are not authorized to view this scan.", "danger")
        return redirect(url_for("my_domains"))

    scan_details = ScanDetails.query.filter_by(scan_id=scan.id).all()

    domains_info = [
        {
            "domain": detail.domain_name,
            "ip_address": detail.ip_address,
            "whois_info": {
                "registrar": detail.whois_registrar,
                "emails": detail.whois_emails,
                "country": detail.whois_country,
                "creation_date": detail.whois_creation_date,
                "name_servers": detail.whois_name_servers
            },
            "similarity_percent": detail.similarity_score,
            "reputation": detail.reputation,
            "vt_link": f"https://www.virustotal.com/gui/domain/{detail.domain_name}"
        }
        for detail in scan_details
    ]

    return render_template(
        "scan_view.html",
        scan=scan,
        results=domains_info,
        found=len([d for d in domains_info if d.get("ip_address") != "---"]),
        total_permutations=scan.permutations_checked,
        domain_input=scan.domain.name
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
