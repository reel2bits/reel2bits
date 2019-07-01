from flask import Blueprint
from flask_restplus import Api
from .v1.accounts import api as api_accounts

blueprint = Blueprint("api_v1", __name__, url_prefix="/api/v1")
api = Api(blueprint, title="Api V1", version="1.0", description="Api V1")

api.add_namespace(api_accounts)
