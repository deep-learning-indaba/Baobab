import flask_restful as restful

from app.utils.auth import auth_required
from app.invoice.repository import InvoiceRepository as invoice_repository

class InvoiceAPI(restful.Resource):
    @auth_required
    def get(self):
        # get invoices for user
        return 200

    @auth_required
    def put(self):
        # cancel invoice?
        return 200

class InvoiceAdminAPI(restful.Resource):
    @auth_required
    def get(self):
        # get invoices for event
        return 200

    @auth_required
    def post(self):
        # create single invoice by event treasurer?
        return 201
    
    @auth_required
    def put(self):
        # update success/fail from webhook
        return 200