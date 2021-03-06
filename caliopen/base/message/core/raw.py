# -*- coding: utf-8 -*-
"""Caliopen core raw message class."""

import hashlib

from caliopen.base.core import BaseUserCore

from caliopen.base.message.model import RawMessage as ModelRaw
from caliopen.base.message.format.mail import MailMessage


class RawMessage(BaseUserCore):

    """
    Raw message core.

    Store in binary form any message before processing
    """

    _model_class = ModelRaw
    _pkey_name = 'raw_id'

    @classmethod
    def create(cls, user, message_id, raw):
        """Create raw message."""
        key = hashlib.sha256(message_id).hexdigest()
        return super(RawMessage, cls).create(user_id=user.user_id,
                                             raw_id=key,
                                             data=raw)

    @classmethod
    def get(cls, user, message_id):
        """Get raw message by message_id."""
        key = hashlib.sha256(message_id).hexdigest()
        return super(RawMessage, cls).get(user, key)

    def parse(self):
        """Parse raw message to get a formatted object."""
        return MailMessage(self.data)
