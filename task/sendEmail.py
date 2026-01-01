import smtplib
import os
import argparse
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import sys

def send_email_with_attachment(sender_email, sender_password, recipient_email, subject, body, attachment_path):
    """
    Sends an email with an audio file attachment.

    Args:
        sender_email (str): The sender's email address
        sender_password (str): The sender's email password or app-specific password
        recipient_email (str): The recipient's email address
        subject (str): The email subject
        body (str): The email body text
        attachment_path (str): Path to the file to be attached
    """
    # Create a multipart message object
    message = MIMEMultipart()

    # Set email headers
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject

    # Add body to email
    message.attach(MIMEText(body, 'plain'))

    # Determine the MIME type based on file extension
    import mimetypes
    ctype, encoding = mimetypes.guess_type(attachment_path)
    if ctype is None or encoding is not None:
        ctype = 'application/octet-stream'

    maintype, subtype = ctype.split('/', 1)

    # Open the file in binary mode and attach it
    with open(attachment_path, "rb") as attachment:
        # Use appropriate MIME type based on the file type
        if maintype == 'audio':
            from email.mime.audio import MIMEAudio
            part = MIMEAudio(attachment.read(), _subtype=subtype)
        elif maintype == 'image':
            from email.mime.image import MIMEImage
            part = MIMEImage(attachment.read(), _subtype=subtype)
        elif maintype == 'text':
            part = MIMEText(attachment.read().decode('utf-8', errors='ignore'), _subtype=subtype)
        else:
            from email.mime.base import MIMEBase
            part = MIMEBase(maintype, subtype)
            part.set_payload(attachment.read())
            encoders.encode_base64(part)

        # Add header as key/value pair to attachment part
        part.add_header(
            'Content-Disposition',
            f'attachment; filename="{os.path.basename(attachment_path)}"',
        )

        # Explicitly set the filename parameter
        part.set_param('name', os.path.basename(attachment_path))

        print(f"Attaching file: {os.path.basename(attachment_path)}")

        # Attach the part to message
        message.attach(part)

    # Create SMTP session for 163.com
    smtp_server = 'smtp.163.com'
    smtp_port = 994  # 163.com uses port 994 for SSL

    try:
        # Create SMTP session with SSL
        server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)
        
        # Login to the server
        server.login(sender_email, sender_password)

        # Convert the multipart message into a string
        text = message.as_string()

        # Send email
        server.sendmail(sender_email, recipient_email, text)
        server.quit()

        print(f"Email sent successfully to {recipient_email}")
        return True
    except smtplib.SMTPAuthenticationError:
        print("Error: Authentication failed. Please check your email and password.")
        return False
    except smtplib.SMTPConnectError:
        print("Error: Failed to connect to the SMTP server.")
        return False
    except smtplib.SMTPRecipientsRefused:
        print("Error: Recipient address was rejected by the server.")
        return False
    except Exception as e:
        print(f"Error occurred while sending email: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Send an audio file via email')
    parser.add_argument('recipient_email', type=str, help='Recipient email address')
    parser.add_argument('--subject', type=str, default='Audio File Attachment', help='Email subject')
    parser.add_argument('--body', type=str, default='Please find the attached audio file.', help='Email body')
    parser.add_argument('--file', type=str, default='对牛弹琴.wav', help='Path to the audio file to send')

    args = parser.parse_args()

    # Get sender credentials
    sender_email = '13815865892@163.com'
    sender_password = 'WLsGGSHSyMv6rzFq'

    if not sender_email or not sender_password:
        print("Error: Please set EMAIL_ADDRESS and EMAIL_PASSWORD environment variables.")
        sys.exit(1)

    # Check if the file exists
    if not os.path.exists(args.file):
        print(f"Error: File {args.file} does not exist.")
        sys.exit(1)

    # Send the email
    success = send_email_with_attachment(
        sender_email=sender_email,
        sender_password=sender_password,
        recipient_email=args.recipient_email,
        subject=args.subject,
        body=args.body,
        attachment_path=args.file
    )

    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()