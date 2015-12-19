# -*- coding: utf-8 -*-
"""Caliopen core thread related classes."""

import logging
import uuid
from datetime import datetime

from caliopen.base.exception import NotFound
from caliopen.base.core import BaseUserCore
from caliopen.base.core.mixin import MixinCoreIndex
from caliopen.base.parameters import ReturnCoreObject, ReturnIndexObject

from caliopen.base.user.core import Contact

from caliopen.base.message.model import  \
    (ThreadExternalLookup as ModelExternalLookup,
     ThreadRecipientLookup as ModelRecipientLookup,
     ThreadMessageLookup as ModelMessageLookup,
     Thread as ModelThread,
     ThreadCounter as ModelCounter,
     IndexedThread)
from caliopen.base.message.parameters import Thread as ThreadParam


log = logging.getLogger(__name__)


def count_attachment(message):
    """Return number of attachment in message."""
    cpt = 0
    if message.parts:
        for p in message.parts:
            if p.filename:
                cpt += 1
    return cpt


class ThreadExternalLookup(BaseUserCore):

    """Lookup thread by external id (facebook, gmail, ...)."""

    _model_class = ModelExternalLookup
    _pkey_name = 'external_id'


class ThreadRecipientLookup(BaseUserCore):

    """Lookup thread for a recipient, only one."""

    _model_class = ModelRecipientLookup
    _pkey_name = 'recipient_name'


class ThreadMessageLookup(BaseUserCore):

    """Lookup thread by external message_id."""

    _model_class = ModelMessageLookup
    _pkey_name = 'external_message_id'


class Counter(BaseUserCore):

    """Counters related to thread."""

    _model_class = ModelCounter

    @classmethod
    def get(cls, user_id, thread_id):
        """Get Counter core object related to a thread_id."""
        try:
            obj = cls._model_class.get(user_id=user_id,
                                       thread_id=thread_id)
            return cls(obj)
        except Exception:
            return None


class Thread(BaseUserCore, MixinCoreIndex):

    """Thread core object."""

    _model_class = ModelThread
    _index_class = IndexedThread

    _pkey_name = 'thread_id'
    _counter = None

    @classmethod
    def create_from_message(cls, user, message):
        new_id = uuid.uuid4()
        contacts = [contact.to_primitive()
                    for contact in message.recipients]
        kwargs = {'user_id': user.user_id,
                  'thread_id': new_id,
                  'date_insert': datetime.utcnow(),
                  'privacy_index': 0,   # XXX to compute somehow
                  'text': message.text[:200],
                  '_indexed_extra': {'date_update': datetime.utcnow(),
                                     'contacts': contacts, }
                  }
        if message.tags:
            kwargs['_indexed_extra']['tags'] = message.tags
        thread = cls.create(**kwargs)
        log.debug('Created thread %s' % thread.thread_id)
        counters = Counter.create(user_id=user.user_id,
                                  thread_id=thread.thread_id)
        counters.model.total_count = 1
        counters.model.unread_count = 1
        counters.model.attachment_count = count_attachment(message)
        counters.save()
        log.debug('Created thread counters %r' % counters)
        return thread

    def update_from_message(self, message):
        # XXX concurrency will have to be considered correctly
        index = self._index_class.get(self.user_id,
                                      self.thread_id)
        if not index:
            log.error('Index not found for thread %s' % self.thread_id)
            raise Exception
        index_data = {
            'text': message.text[:200],
            'date_update': datetime.utcnow(),
        }
        if message.recipients:
            contacts = [x.to_primitive() for x in message.recipients]
            index_data.update({
                'contacts': contacts,
            })
        if message.tags:
            index_data.update({'tags': message.tags})
        index.update({'doc': index_data})
        log.debug('Update index for thread %s' % self.thread_id)
        # Update counters
        counters = Counter.get(self.user_id, self.thread_id)
        counters.model.total_count += 1
        counters.model.unread_count += 1
        nb_attachments = count_attachment(message)
        if nb_attachments:
            counters.model.attachment_count += nb_attachments
        counters.save()
        return True

    @classmethod
    def by_external_id(cls, user, external_thread_id):
        try:
            lookup = ThreadExternalLookup.get(user, external_thread_id)
        except NotFound:
            return None
        return cls.get(user, lookup.thread_id)

    @classmethod
    def by_recipient_name(cls, user, recipient_name):
        try:
            lookup = ThreadRecipientLookup.get(user, recipient_name)
        except NotFound:
            return None
        return cls.get(user, lookup.thread_id)

    @classmethod
    def expand_contacts(self, user, contacts):
        results = []
        for contact in contacts:
            results.append(Contact.get(user, contact['contact_id']))
        return results

    @classmethod
    def expand_tags(self, user, tags):
        if not tags:
            return []
        user_tags = dict((x.label, x) for x in user.tags)
        results = []
        for tag in tags:
            if tag in user_tags:
                results.append(user_tags[tag])
            else:
                log.warn('Unknow user tag %r' % tag)
        return results

    @property
    def counters(self):
        """return ``Counter`` core related to threads."""
        # XXX need of a reify decorator ?
        if not self._counter:
            self._counter = Counter.get(self.user_id, self.thread_id)
        return self._counter

    @property
    def total_count(self):
        """Total messages counter."""
        return self.counters.total_count

    @property
    def unread_count(self):
        """Unread messages counter."""
        return self.counters.unread_count

    @property
    def attachment_count(self):
        """Total number of attachments."""
        return self.counters.attachment_count

    @property
    def contacts(self):
        if self._index_data:
            return self._index_data.get('contacts', [])
        return []

    @property
    def tags(self):
        if self._index_data:
            return self._index_data.get('tags', [])
        return []

    @classmethod
    def main_view(cls, user, limit, offset):
        """Build the main view results."""
        index_threads = cls.find_index(user, None,
                                       limit=limit,
                                       offset=offset)

        core_threads = [cls.get(user, x['thread_id'], index_data=x)
                        for x in index_threads['data']]
        return {'threads': core_threads, 'total': index_threads['total']}


class ReturnIndexThread(ReturnIndexObject):

    _index_class = IndexedThread
    _return_class = ThreadParam


class ReturnThread(ReturnCoreObject):

    _core_class = Thread
    _return_class = ThreadParam
