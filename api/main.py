from app import app
application = app  # make uwsgi happy
if __name__ == "__main__":
    app.run()