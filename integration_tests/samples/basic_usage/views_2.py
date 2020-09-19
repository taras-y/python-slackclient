# ------------------
# Only for running this script here
import json
import logging
import sys
from os.path import dirname

sys.path.insert(1, f"{dirname(__file__)}/../../..")
logging.basicConfig(level=logging.DEBUG)

# ---------------------
# Slack WebClient
# ---------------------

import os

from slack import WebClient
from slack.errors import SlackApiError
from slack.signature import SignatureVerifier
from slack.web.classes.blocks import InputBlock
from slack.web.classes.elements import PlainTextInputElement
from slack.web.classes.objects import PlainTextObject
from slack.web.classes.views import View

client = WebClient(token=os.environ["SLACK_API_TOKEN"])
signature_verifier = SignatureVerifier(os.environ["SLACK_SIGNING_SECRET"])

# ---------------------
# Flask App
# ---------------------

# pip3 install flask
from flask import Flask, request, make_response

app = Flask(__name__)


@app.route("/slack/events", methods=["POST"])
def slack_app():
    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        return make_response("invalid request", 403)

    if "payload" in request.form:
        payload = json.loads(request.form["payload"])
        if payload["type"] == "shortcut" \
            and payload["callback_id"] == "open-modal-shortcut":
            # Open a new modal by a global shortcut
            try:
                view = View(
                    type="modal",
                    callback_id="modal-id",
                    title=PlainTextObject(text="Awesome Modal"),
                    submit=PlainTextObject(text="Submit"),
                    close=PlainTextObject(text="Cancel"),
                    blocks=[
                        InputBlock(
                            block_id="b-id",
                            label=PlainTextObject(text="Input label"),
                            element=PlainTextInputElement(action_id="a-id")
                        )
                    ]
                )
                api_response = client.views_open(
                    trigger_id=payload["trigger_id"],
                    view=view,
                )
                return make_response("", 200)
            except SlackApiError as e:
                code = e.response["error"]
                return make_response(f"Failed to open a modal due to {code}", 200)

        if payload["type"] == "view_submission" \
            and payload["view"]["callback_id"] == "modal-id":
            # Handle a data submission request from the modal
            submitted_data = payload["view"]["state"]["values"]
            print(submitted_data)  # {'b-id': {'a-id': {'type': 'plain_text_input', 'value': 'your input'}}}
            return make_response("", 200)

    return make_response("", 404)


if __name__ == "__main__":
    # export SLACK_SIGNING_SECRET=***
    # export SLACK_API_TOKEN=xoxb-***
    # export FLASK_ENV=development
    # python3 integration_tests/samples/basic_usage/views_2.py
    app.run("localhost", 3000)

# ngrok http 3000
