import io
import json
from datetime import datetime

from flask_mail import Message
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle

from app import mail


def send_alert_email_with_summary(user, scans_with_alerts):
    buffer_pdf = io.BytesIO()
    buffer_txt = io.StringIO()

    doc = SimpleDocTemplate(buffer_pdf, pagesize=A4, title=f"Alert Summary Report for {user.email}")
    elements = []
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']

    elements.append(Paragraph(f"Alert Summary Report for {user.email}", title_style))
    elements.append(Paragraph(f"Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    elements.append(Paragraph(" ", normal_style))

    buffer_txt.write(f"Alerted Domains Report for {user.email}\n")
    buffer_txt.write(f"Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    for scan in scans_with_alerts:
        elements.append(Paragraph(f"Domain: {scan.domain.name}", subtitle_style))
        elements.append(Paragraph(f"Scan Date: {scan.date}", normal_style))
        elements.append(Paragraph("Alerted Domains:", normal_style))

        alerted_domains = json.loads(scan.domains_alerted) if scan.domains_alerted else []

        buffer_txt.write(f"Domain: {scan.domain.name}\n")
        buffer_txt.write(f"Scan Date: {scan.date}\n")
        for domain in alerted_domains:
            buffer_txt.write(f"{domain}\n")
        buffer_txt.write("\n")

        table_data = [["#", "Domain"]]
        for idx, domain in enumerate(alerted_domains, start=1):
            table_data.append([idx, domain])

        table = Table(table_data, colWidths=[30, 400])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ]))

        elements.append(table)
        elements.append(Paragraph(" ", normal_style))

    doc.build(elements)
    buffer_pdf.seek(0)
    buffer_txt.seek(0)

    alert_message = (f"Multiple typosquatting domains have been detected.\nPlease see the attached PDF and TXT files "
                     f"for details.")
    msg = Message(
        subject="Scheduled Scan Alert",
        sender="typosquattingtest@gmail.com",
        recipients=[user.alert_email],
        body=f"Dear {user.email},\n\n{alert_message}\n\nBest regards,\nYour Security Team"
    )

    msg.attach(
        filename="scan_report.pdf",
        content_type="application/pdf",
        data=buffer_pdf.read()
    )

    msg.attach(
        filename="alerted_domains.txt",
        content_type="text/plain",
        data=buffer_txt.getvalue()
    )

    try:
        mail.send(msg)
        print(f"[INFO] Email sent to {user.alert_email} with attached scan report and domain list.")
    except Exception as e:
        print(f"[ERROR] Failed to send email to {user.alert_email}: {e}")



    except Exception as e:
        print(f"Failed to send alert: {e}")
