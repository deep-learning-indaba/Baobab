import traceback
from app import LOGGER
from config import SMTP_USERNAME, SMTP_PASSWORD, SMTP_SENDER_NAME, SMTP_SENDER_EMAIL, SMTP_HOST, SMTP_PORT, DEBUG
import smtplib
import email.utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_mail(recipient, subject, body_text, body_html='', charset='UTF-8', mail_type='AMZ'):
    '''[summary]
    
    Arguments:
        recipient {[type]} -- [description]
        subject {[type]} -- [description]
        body_text {[type]} -- [description]
    
    Keyword Arguments:
        body_html {[type]} -- [description] (default: {None})
        type {str} -- [description] (default: {'AMZ'})
    
    Raises:
        e -- [description]
    '''
    LOGGER.debug("Entered mailer")
    if (not DEBUG):
        if mail_type == 'AMZ':
            configuration_set = 'ConfigSet'
            try:
                LOGGER.info("Building Mimemultipart msg")
                msg = MIMEMultipart()
                LOGGER.info("Setting subject %s"%(subject,))
                msg['Subject'] = subject
                LOGGER.info("Setting Sender name : %s and Sender email %s"%(SMTP_SENDER_NAME, SMTP_SENDER_EMAIL))
                msg['From'] = email.utils.formataddr((SMTP_SENDER_NAME, SMTP_SENDER_EMAIL))
                LOGGER.info("Setting recipient %s"%(recipient))
                msg['To'] = recipient
                #msg.add_header('X-SES-CONFIGURATION-SET', configuration_set)

                LOGGER.info("Setting body for the mime msg")
                body_part1 = MIMEText(body_text, 'plain', _charset=charset)
                body_part2 = MIMEText(body_html, 'html', _charset=charset)

                LOGGER.info("Attaching body to the the mime msg")
                msg.attach(body_part1)
                msg.attach(body_part2)

                LOGGER.info("Creating SMTP object with host %s and port %s"%(SMTP_HOST, SMTP_PORT))
                server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
                server.ehlo()
                LOGGER.info("Setting smtp to TTLS mode")
                server.starttls()
                server.ehlo()
                LOGGER.info("Setting username and password for the SMTP connection")
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                LOGGER.info("Sending email ")
                server.sendmail(SMTP_SENDER_EMAIL, recipient, msg.as_string())
                server.close()
            except Exception as e:
                LOGGER.error(traceback.format_exc())
                raise e
            else:
                LOGGER.info("Email sent successfully ")
    else:
        LOGGER.debug('Recipient : {recipient}'.format(recipient=recipient))
        LOGGER.debug('Subject : {subject}'.format(subject=subject))
        LOGGER.debug('Body : {body}'.format(body=body_text))


'''
if __name__=="__main__":
    send_mail(recipient='nischal.hp@gmail.com', subject='TestSMTPEmail', body_text='Dear user, Please use the following link to successfully reset your password : www.placeholder.com/ResetPassword?resetToken=[reset_password_token].')
'''
