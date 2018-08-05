from little_boxes import activitypub as ap
from flask import current_app, g
import requests


class Reel2BitsBackend(ap.Backend):

    def debug_mode(self) -> bool:
        return current_app.config['DEBUG']

    def user_agent(self) -> str:
        url = current_app.config['BASE_URL']
        return f"{requests.utils.default_user_agent()} " \
               f"(reel2bits/{g.cfg['REEL2BITS_VERSION_VER']}; +{url})"

    def base_url(self):
        return current_app.config['BASE_URL']

    def activity_url(self, obj_id: str):
        return f"{self.base_url()}/outbox/{obj_id}"

    def note_url(self, obj_id: str):
        return f"{self.base_url()}/note/{obj_id}"
