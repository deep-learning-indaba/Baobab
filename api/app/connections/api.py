from flask import g, request
import flask_restful as restful
from flask_restful import reqparse

from app import db
from app.utils.auth import auth_required
from app.utils import errors
from app.utils.push import push_to_user
from app.connections.models import ConnectionStatus
from app.connections.repository import ConnectionRepository
from app.attendance.repository import AttendanceRepository, QRTokenRepository
from app.profiles.repository import ProfileRepository
from app.invitedGuest.repository import InvitedGuestRepository
from app.users.repository import UserRepository
from app.events.repository import EventRepository


def _connection_state(event_id, me_id, other_id):
    """Return (state_str, direction_str) describing the connection between me and other."""
    my_row = ConnectionRepository.get(event_id, me_id, other_id)
    their_row = ConnectionRepository.get(event_id, other_id, me_id)

    if my_row and my_row.status == ConnectionStatus.BLOCKED:
        return 'blocked', None
    if my_row and my_row.status == ConnectionStatus.CONNECTED:
        return 'connected', None
    if my_row and my_row.status == ConnectionStatus.PENDING:
        return 'outgoing_pending', 'outgoing'
    if their_row and their_row.status == ConnectionStatus.PENDING:
        return 'incoming_pending', 'incoming'
    return 'none', None


def _serialize_target(target_user, profile, role, connection_state, direction):
    if profile and profile.visibility == 'hidden':
        target_data = {
            'user_id': target_user.id,
            'firstname': target_user.firstname,
            'lastname': target_user.lastname,
            'role': role,
            'photo_url': profile.photo_url if profile else None,
            'hidden': True,
        }
    else:
        links = {}
        if profile and profile.links:
            for lnk in profile.links:
                links[lnk.link_type] = lnk.url
        target_data = {
            'user_id': target_user.id,
            'firstname': target_user.firstname,
            'lastname': target_user.lastname,
            'role': role,
            'photo_url': profile.photo_url if profile else None,
            'headline': profile.headline if profile else None,
            'affiliation': profile.affiliation if profile else None,
            'links': links,
            'hidden': False,
        }
    return {
        'target': target_data,
        'connection': {'state': connection_state, 'direction': direction},
        'is_self': False,
    }


def _serialize_connection_row(row, me_id, event_id):
    """Serialize a Connection row with the other user's basic profile info."""
    other_id = row.to_user_id if row.from_user_id == me_id else row.from_user_id
    user = UserRepository.get_by_id(other_id)
    profile = ProfileRepository.get(other_id)
    ig = InvitedGuestRepository.get_for_event_and_user(event_id, other_id)
    role = ig.role if ig else 'General Attendee'
    return {
        'connection_id': row.id,
        'user_id': other_id,
        'firstname': user.firstname if user else '',
        'lastname': user.lastname if user else '',
        'role': role,
        'photo_url': profile.photo_url if profile else None,
        'headline': profile.headline if profile else None,
        'status': row.status.value,
        'direction': 'outgoing' if row.from_user_id == me_id else 'incoming',
        'updated_at': row.updated_at.isoformat() + 'Z',
    }


class ConnectionResolveAPI(restful.Resource):
    @auth_required
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        req_parser.add_argument('t', type=str, required=True)
        args = req_parser.parse_args()
        event_id = args['event_id']
        me_id = g.current_user['id']

        if not AttendanceRepository.is_confirmed_guest(event_id, me_id):
            return errors.NOT_A_GUEST

        qr = QRTokenRepository.resolve(args['t'])
        if qr is None or qr.event_id != event_id:
            return errors.INVALID_QR

        target_id = qr.user_id

        if target_id == me_id:
            return {'is_self': True, 'target': None, 'connection': None}, 200

        target_user = UserRepository.get_by_id(target_id)
        if target_user is None:
            return errors.USER_NOT_FOUND

        profile = ProfileRepository.get(target_id)
        ig = InvitedGuestRepository.get_for_event_and_user(event_id, target_id)
        role = ig.role if ig else 'General Attendee'

        state, direction = _connection_state(event_id, me_id, target_id)
        return _serialize_target(target_user, profile, role, state, direction), 200


class ConnectionAPI(restful.Resource):
    @auth_required
    def post(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        req_parser.add_argument('to_user_id', type=int, required=True)
        args = req_parser.parse_args()
        event_id = args['event_id']
        me_id = g.current_user['id']
        to_id = args['to_user_id']

        if not AttendanceRepository.is_confirmed_guest(event_id, me_id):
            return errors.NOT_A_GUEST

        if me_id == to_id:
            return errors.CANNOT_CONNECT_SELF

        if ConnectionRepository.is_blocked(event_id, me_id, to_id):
            return errors.CONNECTION_BLOCKED

        ConnectionRepository.upsert_request(event_id, me_id, to_id)

        target_user = UserRepository.get_by_id(to_id)
        me_user = UserRepository.get_by_id(me_id)
        event = EventRepository.get_by_id(event_id)
        if target_user and me_user and event:
            try:
                push_to_user(to_id, {
                    'title': 'New connection request',
                    'body': '{} {} wants to connect with you.'.format(
                        me_user.firstname, me_user.lastname),
                    'url': '/{}/app/connections'.format(event.key),
                })
            except Exception:
                pass

        return {'status': 'pending'}, 201


class ConnectionRespondAPI(restful.Resource):
    @auth_required
    def post(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        req_parser.add_argument('from_user_id', type=int, required=True)
        req_parser.add_argument('action', type=str, required=True)
        args = req_parser.parse_args()
        event_id = args['event_id']
        me_id = g.current_user['id']
        from_id = args['from_user_id']
        action = args['action']

        if action not in ('accept', 'reject', 'block'):
            return {'message': 'action must be accept, reject, or block'}, 400

        if not AttendanceRepository.is_confirmed_guest(event_id, me_id):
            return errors.NOT_A_GUEST

        # The row is from_id → me_id
        row = ConnectionRepository.get(event_id, from_id, me_id)
        if row is None or row.status not in (ConnectionStatus.PENDING, ConnectionStatus.CONNECTED):
            return errors.CONNECTION_NOT_FOUND

        if action == 'accept':
            ConnectionRepository.set_status(event_id, from_id, me_id, ConnectionStatus.CONNECTED)
            ConnectionRepository.set_status(event_id, me_id, from_id, ConnectionStatus.CONNECTED)
            me_user = UserRepository.get_by_id(me_id)
            event = EventRepository.get_by_id(event_id)
            if me_user and event:
                try:
                    push_to_user(from_id, {
                        'title': 'Connection accepted',
                        'body': '{} {} connected with you.'.format(
                            me_user.firstname, me_user.lastname),
                        'url': '/{}/app/connections'.format(event.key),
                    })
                except Exception:
                    pass
        elif action == 'reject':
            ConnectionRepository.set_status(event_id, from_id, me_id, ConnectionStatus.REJECTED)
        elif action == 'block':
            ConnectionRepository.set_status(event_id, from_id, me_id, ConnectionStatus.BLOCKED)

        return {'status': action + 'ed'}, 200


class ConnectionWithdrawAPI(restful.Resource):
    @auth_required
    def post(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        req_parser.add_argument('to_user_id', type=int, required=True)
        args = req_parser.parse_args()
        event_id = args['event_id']
        me_id = g.current_user['id']
        to_id = args['to_user_id']

        row = ConnectionRepository.get(event_id, me_id, to_id)
        if row is None or row.status != ConnectionStatus.PENDING:
            return errors.CONNECTION_NOT_FOUND

        ConnectionRepository.set_status(event_id, me_id, to_id, ConnectionStatus.WITHDRAWN)
        return {'status': 'withdrawn'}, 200


class ConnectionListAPI(restful.Resource):
    @auth_required
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        args = req_parser.parse_args()
        event_id = args['event_id']
        me_id = g.current_user['id']

        if not AttendanceRepository.is_confirmed_guest(event_id, me_id):
            return errors.NOT_A_GUEST

        rows = ConnectionRepository.list_for_user(event_id, me_id)

        incoming = []
        outgoing = []
        connected_ids = set()
        connected = []
        scanned_history = []

        for row in rows:
            s = _serialize_connection_row(row, me_id, event_id)
            if row.status == ConnectionStatus.PENDING:
                if row.to_user_id == me_id:
                    incoming.append(s)
                else:
                    outgoing.append(s)
            elif row.status == ConnectionStatus.CONNECTED:
                other_id = row.to_user_id if row.from_user_id == me_id else row.from_user_id
                if other_id not in connected_ids:
                    connected_ids.add(other_id)
                    connected.append(s)
            if row.from_user_id == me_id:
                scanned_history.append(s)

        return {
            'incoming': incoming,
            'outgoing': outgoing,
            'connected': connected,
            'scanned_history': scanned_history,
        }, 200


class ConnectionReportAPI(restful.Resource):
    @auth_required
    def post(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        req_parser.add_argument('reported_user_id', type=int, required=True)
        req_parser.add_argument('reason', type=str, required=False)
        args = req_parser.parse_args()
        event_id = args['event_id']
        me_id = g.current_user['id']

        if not AttendanceRepository.is_confirmed_guest(event_id, me_id):
            return errors.NOT_A_GUEST

        ConnectionRepository.create_report(event_id, me_id, args['reported_user_id'], args.get('reason'))
        return {'status': 'reported'}, 201
