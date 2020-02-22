from markdown2 import Markdown
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from premailer import transform
from argparse import ArgumentParser
from bs4 import BeautifulSoup

EMAIL_TEMPLATE_DIR = '../templates/email/'

def create_HTML(email_template='template.html'):

	# with open(EMAIL_TEMPLATE_DIR + markdown_file) as f:
	# 	all_content = f.readlines() markdown_file='default.md'

	# Get the title line and clean it up
	#title_line = all_content[0]
	#title = f'My Newsletter - {title_line[7:].strip()}'

	# Parse out the body from the meta data content at the top of the file
	#body_content = all_content[6:]

	# Create a markdown object and convert the list of file lines to HTML
	#markdowner = Markdown()
	#markdown_content = markdowner.convert(''.join(body_content))

	# Set up jinja templates
	env = Environment(loader=FileSystemLoader(EMAIL_TEMPLATE_DIR))
	template = env.get_template(email_template)

	# Define the template variables and render
	#template_vars1 = {'email_content': markdown_content, 'title': title}

	email_content = 'This is an email to inform you that........'
	sender ='deeplearning@indaba'
	title = 'Email template'
	template_vars = {'email_content':email_content ,'SenderInfoLine':sender, 'title':title }
	raw_html = template.render(template_vars)
	

	# Generate the final output string
	# Inline all the CSS using premailer.transform
	# Use BeautifulSoup to make the formatting nicer
	soup = BeautifulSoup(transform(raw_html),
	'html.parser').prettify(formatter="html")
	
	
	# The unsubscribe tag gets mangled. Clean it up.
	final_HTML = str(soup).replace('%7B%7BUnsubscribeURL%7D%7D',
	'{{UnsubscribeURL}}')

	return final_HTML


if __name__ == '__main__':
    print('Creating output HTML')
    print(create_HTML())
    print('Completed')