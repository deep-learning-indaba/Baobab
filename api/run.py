#!/usr/bin/env python

import sys

from flask_failsafe import failsafe


@failsafe
def create_app():
    from app import manager

    return manager


# Remove encoding if upgrading to python 3.
if __name__ == "__main__":
    create_app().run()
