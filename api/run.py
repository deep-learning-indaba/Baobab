from flask_failsafe import failsafe


@failsafe
def create_app():
    from app import manager
    return manager


if __name__ == '__main__':
    create_app().run()
