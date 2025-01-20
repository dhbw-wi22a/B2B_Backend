import json
import os
import logging
import requests

logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()

MAILSERVICE_BASE_URL = os.getenv('MAILSERVICE_BASE_URL')
MAILSERVICE_REGISTRATION_ENDPOINT = os.getenv('MAILSERVICE_REGISTRATION_ENDPOINT')
MAILSERVICE_GROUP_INVITATION_ENDPOINT = os.getenv('MAILSERVICE_GROUP_INVITATION_ENDPOINT')
MAILSERVICE_ORDER_CONFIRMATION_ENDPOINT = os.getenv('MAILSERVICE_ORDER_CONFIRMATION_ENDPOINT')
SHOP_BASE_URL = os.getenv('SHOP_BASE_URL')

headers = {'Content-Type': 'application/json'}

def send_registration_mail(user):
    """
        Send an email verification for a new registered user.
        """
    reg_url = f"{MAILSERVICE_BASE_URL}/{MAILSERVICE_REGISTRATION_ENDPOINT}"
    verification_link = f"{SHOP_BASE_URL}/web/api/verify-email/{user.verification_token.token}"

    payload = {
        "recipients": [
            {
                "email": user.email,
                "fname": user.first_name,
                "lname": user.last_name,
                "verification_link": verification_link
            }
        ]
    }

    try:
        response = requests.post(
                reg_url,
                headers=headers,
                json=payload)

        response.raise_for_status()
        logger.info("Email sent successfully")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending email: {e}")
        return None


def send_group_invitation_mail(invitation):
    """
    Send an email invitation for a group membership.
    """
    invitation_url = f"{MAILSERVICE_BASE_URL}/{MAILSERVICE_GROUP_INVITATION_ENDPOINT}"
    invitation_link = f"{SHOP_BASE_URL}/web/api/group/invitations/{invitation.group_invite_token}"

    # Prepare payload
    payload = {
        "recipients": [
            {
                "email": invitation.email,
                "fname": invitation.invited_by.first_name,
                "lname": invitation.invited_by.last_name,
                "group_name": invitation.group.name,
                "invited_by": f"{invitation.invited_by.first_name} {invitation.invited_by.last_name}",
                "invitation_link": invitation_link
            }
        ]
    }

    try:
        response = requests.post(
            invitation_url,
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        logger.info("Group invitation email sent successfully")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending group invitation email: {e}")
        return None



def send_order_conf_mail():
    order_conf_url = f"{MAILSERVICE_BASE_URL}/{MAILSERVICE_ORDER_CONFIRMATION_ENDPOINT}"
