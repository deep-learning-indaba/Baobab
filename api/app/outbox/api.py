import flask_restful as restful
from flask import request

from app import LOGGER
from app.outbox.sender import deliver_pending
from app.utils import errors


def is_scheduler_request():
    """Whether this request came from the App Engine cron scheduler.

    App Engine strips X-Appengine-Cron from anything arriving over the public
    internet, so its presence can only come from the scheduler itself.
    """
    return request.headers.get('X-Appengine-Cron') == 'true'


class OutboxWorkerAPI(restful.Resource):
    """POST /api/v1/tasks/outbox — deliver queued emails and push notifications.

    Driven every minute by App Engine cron (api/cron.yaml). Each run is bounded
    by a time budget, so a backlog drains over several runs instead of one long
    request.
    """

    def post(self):
        if not is_scheduler_request():
            return errors.FORBIDDEN

        summary = deliver_pending()
        LOGGER.info('Outbox run complete: %s', summary)
        return summary, 200
