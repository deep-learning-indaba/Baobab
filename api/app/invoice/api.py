import flask_restful as restful

from app.invoice.mixins import InvoiceMixin, InvoiceAdminMixin
from app.utils.auth import auth_required
from app.invoice.repository import InvoiceRepository as invoice_repository
from app.users.repository import UserRepository as user_repository
from app.utils.errors import FORBIDDEN

class InvoiceAPI(InvoiceMixin, restful.Resource):
    @auth_required
    def get(self):
        args = self.req_parser.parse_args()
        invoice_id = args['invoice_id']

        user_id = g.current_user["id"]
        current_user = user_repository.get_by_id(user_id)

        invoice = invoice_repository.get_one_for_customer(invoice_id, current_user.email)
        return invoice, 200

    @auth_required
    def delete(self):
        args = self.req_parser.parse_args()

        user_id = g.current_user["id"]
        current_user = user_repository.get_by_id(user_id)

        invoice = invoice_repository.get_one_for_customer(args['invoice_id'], current_user.email)
        invoice.cancel(user_id)
        invoice_repository.save(invoice)

        return 200


class InvoiceListAPI(restful.Resource):
    @auth_required
    def get(self):
        current_user = user_repository.get_by_id(g.current_user["id"])
        invoices = invoice_repository.get_all_for_customer(current_user.email)
        return invoices, 200


class InvoiceAdminAPI(InvoiceAdminMixin, restful.Resource):
    @auth_required
    def get(self):
        args = self.get_parser.parse_args()
        event_id = args['event_id']

        user_id = g.current_user["id"]
        current_user = user_repository.get_by_id(user_id)

        if not current_user.is_event_treasurer(event_id):
            return FORBIDDEN

        invoices = invoice_repository.get_for_event(event_id)
        return invoices, 200

    @auth_required
    def post(self):
        # create single invoice by event treasurer?
        return 201
    
    @auth_required
    def put(self):
        # update success/fail from webhook
        return 200