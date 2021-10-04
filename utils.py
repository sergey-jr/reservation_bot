from datetime import datetime

from telegram import Update
from telegram.ext import CallbackContext

import settings
from db import Person, Reservation


def get_current_user_for_mh(func):
    def wrapper(update: Update, context: CallbackContext):
        user_data = update.message.from_user
        query = settings.session.query(Person).filter(Person.user_id == user_data.id)
        current_person = query.all()
        if not current_person:
            update.message.reply_text('Сначала зарегиструйтесь')
        else:
            current_person = query.one()
            return func(update, context, current_person)

    return wrapper


def get_current_user_for_qh(func):
    def wrapper(update: Update, context: CallbackContext):
        query = update.callback_query
        user_data = query.from_user
        query_set = settings.session.query(Person).filter(Person.user_id == user_data.id)
        current_person = query_set.all()
        if not current_person:
            query.answer('Сначала зарегиструйтесь')
        else:
            current_person = query_set.one()
            return func(update, context, current_person)

    return wrapper


def get_reservations_for_user(update: Update, context: CallbackContext, current_person):
    now = datetime.now()
    return settings.session.query(Reservation). \
        filter(Reservation.date_start >= now,
               Reservation.person_id == current_person.id,
               Reservation.removed == False).all()
