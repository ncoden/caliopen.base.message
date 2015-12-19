# -*- coding: utf-8 -*-
"""Caliopen storage model for messages."""

from cassandra.cqlengine import columns

from caliopen.base.store.model import BaseModel, BaseIndexDocument
from caliopen.base.store.mixin import IndexTagMixin


class RawMessage(BaseModel):

    """Raw message model."""

    user_id = columns.UUID(primary_key=True)
    raw_id = columns.Text(primary_key=True)
    data = columns.Bytes()


class Thread(BaseModel):

    """Thread to group messages model."""

    # XXX threading simplest model, most data are only in index
    user_id = columns.UUID(primary_key=True)
    thread_id = columns.UUID(primary_key=True)
    date_insert = columns.DateTime()
    privacy_index = columns.Integer()
    importance_level = columns.Integer()
    text = columns.Text()


class ThreadCounter(BaseModel):

    """Counters related to thread."""
    user_id = columns.UUID(primary_key=True)
    thread_id = columns.UUID(primary_key=True)
    total_count = columns.Counter()
    unread_count = columns.Counter()
    attachment_count = columns.Counter()


class ThreadRecipientLookup(BaseModel):

    """Lookup thread by a recipient name."""

    # XXX temporary, until a recipients able lookup can be design
    user_id = columns.UUID(primary_key=True)
    recipient_name = columns.Text(primary_key=True)
    thread_id = columns.UUID()


class ThreadExternalLookup(BaseModel):

    """Lookup thread by external_thread_id."""

    user_id = columns.UUID(primary_key=True)
    external_id = columns.Text(primary_key=True)
    thread_id = columns.UUID()


class ThreadMessageLookup(BaseModel):

    """Lookup thread by external message_id."""

    user_id = columns.UUID(primary_key=True)
    external_message_id = columns.Text(primary_key=True)
    thread_id = columns.UUID()
    message_id = columns.UUID()


class Message(BaseModel):

    """Message model."""

    user_id = columns.UUID(primary_key=True)
    message_id = columns.UUID(primary_key=True)
    thread_id = columns.UUID()
    type = columns.Text()
    from_ = columns.Text()
    date = columns.DateTime()
    date_insert = columns.DateTime()
    privacy_index = columns.Integer()
    privacy_features = columns.Map(columns.Text(), columns.Text())
    importance_level = columns.Integer()
    subject = columns.Text()  # Subject of email, the message for short
    external_message_id = columns.Text()
    external_parent_id = columns.Text()
    external_thread_id = columns.Text()
    tags = columns.List(columns.Text)
    flags = columns.List(columns.Text)  # Seen, Recent, Deleted, ... IMAP?
    offset = columns.Integer()


class IndexedMessage(BaseIndexDocument, IndexTagMixin):

    """Message from index server with helpers methods."""

    doc_type = 'messages'
    columns = ['message_id', 'type',
               'external_message_id', 'thread_id',
               'privacy_index', 'importance_level',
               'subject', 'from_', 'date', 'date_insert',
               'text', 'size', 'answer_to', 'offset', 'headers',
               'tags', 'flags', 'parts', 'contacts',
               ]


class IndexedThread(BaseIndexDocument, IndexTagMixin):

    """Thread from index server."""

    columns = ['thread_id', 'date_insert', 'date_update',
               'privacy_index', 'importance_level',
               'text', 'tags', 'contacts']

    doc_type = 'threads'
