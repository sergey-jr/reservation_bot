from datetime import datetime

from telegram import Update
from telegram.ext import CallbackContext

import settings
from db import Person, Reservation
from messages import ErrorMessage


def get_current_user(func):
    def wrapper(update: Update, context: CallbackContext):
        if update.message:
            holder = update.message
        if update.callback_query:
            holder = update.callback_query

        user_data = holder.from_user
        query = settings.session.query(Person).filter(Person.user_id == user_data.id)
        current_person = query.all()
        if not current_person:
            update.message.reply_text(ErrorMessage.registration.value)
        else:
            current_person = query.one()
            return func(update, context, current_person)

    return wrapper


def get_reservations_for_user(update: Update, context: CallbackContext, current_person):
    now = datetime.now()
    return settings.session.query(Reservation). \
        filter(Reservation.date_start >= now,
               Reservation.person_id == current_person.id,
               Reservation.removed == False).all()
