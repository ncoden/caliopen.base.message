# -*- coding: utf-8 -*-
"""Caliop core user's messages."""
from __future__ import absolute_import, print_function, unicode_literals
import logging
import uuid

from datetime import datetime


from caliopen.base.core import BaseUserCore
from caliopen.base.core.mixin import MixinCoreIndex
from caliopen.base.parameters import ReturnCoreObject, ReturnIndexObject

from caliopen.base.message.model import Message as ModelMessage, IndexedMessage
from caliopen.base.message.core.raw import RawMessage
from caliopen.base.message.parameters import Message as ParamMessage


log = logging.getLogger(__name__)


class PrivacyIndexCompute(object):

    """Class for compute of privacy_index."""

    _message_type_pi = {
        'mail': 10,
    }

    def __init__(self, message):
        self.message = message
        self.features = message.privacy_features

    def get_index(self):
        """Compute privacy index for a message."""
        # XXX do better
        pi = self._message_type_pi.get(self.message.type, 0)
        if 'PGP' in self.features.get('content_privacy', ''):
            pi += 20
        if self.features.get('transport_security'):
            pi += 10
        return pi

    def get_features(self):
        """Return formatted features for storage."""
        return dict((k, v) for k, v in self.features.items() if v)


class Message(BaseUserCore, MixinCoreIndex):

    """Message core object."""

    _model_class = ModelMessage
    _index_class = IndexedMessage
    _pkey_name = 'message_id'

    @classmethod
    def create(cls, user, message, thread, lookup):
        """Create a new message for a given user and thread."""
        message.validate()
        picomp = PrivacyIndexCompute(message)
        parent_id = message.external_parent_id
        message_id = uuid.uuid4()
        answer_to = lookup.message_id if lookup else None

        # TODO : index parts information
        extras = {'headers': message.headers,
                  'text': message.text,
                  'answer_to': answer_to,
                  'contacts': [contact.to_primitive()
                               for contact in message.recipients],
                  'date': message.date,
                  'size': message.size,
                  'from_': message.from_}
        msg = super(Message, cls).create(user_id=user.user_id,
                                         message_id=message_id,
                                         thread_id=thread.thread_id,
                                         type=message.type,
                                         from_=message.from_,
                                         date=message.date,
                                         date_insert=datetime.utcnow(),
                                         privacy_index=picomp.get_index(),
                                         privacy_features=picomp.get_features(),
                                         importance_level=
                                            message.importance_level,
                                         subject=message.subject,
                                         external_message_id=
                                            message.external_message_id,
                                         external_parent_id=parent_id,
                                         tags=message.tags,
                                         flags=[r'Recent'],
                                         lookup=lookup,
                                         # Indexed fields
                                         _indexed_extra=extras
                                         )
        return msg

    @classmethod
    def by_thread_id(cls, user, thread_id, order=None, limit=None, offset=0):
        """Get messages for a given thread from index."""
        params = {'thread_id': thread_id}
        messages = cls._index_class.filter(user.user_id, params,
                                           order=order,
                                           limit=limit,
                                           offset=0)
        return messages

    @property
    def text(self):
        """Return text from message."""
        # XXX do not use RawMail lookup
        raw = RawMessage.get(self.user, str(self.external_message_id))
        msg = raw.parse()
        return msg.text


class ReturnMessage(ReturnCoreObject):

    """Return parameter from a core message."""

    _core_class = Message
    _return_class = ParamMessage


class ReturnIndexMessage(ReturnIndexObject):

    """Return parameter from an indexed message."""

    _index_class = IndexedMessage
    _return_class = ParamMessage
