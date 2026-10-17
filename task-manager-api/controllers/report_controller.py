"""Controller de relatórios (PB-05)."""
from flask import jsonify

from services import report_service, user_service


def summary_report():
    return jsonify(report_service.summary_report()), 200


def user_report(user_id):
    user = user_service.get_user(user_id)
    return jsonify(report_service.user_report(user)), 200
