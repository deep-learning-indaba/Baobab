#Define and create string builders here

def build_response_email_subject(title, firstname, lastname):
    return (f'Dear {title} {firstname} {lastname}, ')

def build_response_email_body(event_description, event_name, summary):
    return f"""Thank you for applying to attend {event_description}. Your application is being reviewed by our committee and we will get back to you as soon as possible. Included below is a copy of your responses.
        \n\n {summary} \n\n
        Kind Regards, \n
        The {event_name} Organising Committee"""