import logging
from datetime import datetime

from sqlalchemy.sql import func
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters

import settings
from db import Person, Reservation
from utils import get_reservations_for_user, get_current_user_for_qh, get_current_user_for_mh

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext) -> None:
    keyboard = [[KeyboardButton('Зарегистрироваться', request_contact=True), KeyboardButton('Зарезервировать')],
                [KeyboardButton('Список бронирований'), KeyboardButton('Отменить бронирование'),
                 KeyboardButton('Отменить все бронирования')],
                [KeyboardButton('help')]]

    reply_markup = ReplyKeyboardMarkup(keyboard)
    update.message.reply_text('Меню', reply_markup=reply_markup)


def help_command(update: Update, context: CallbackContext):
    update.message.reply_text("Бот для резервирования столиков в ресторане. Используйте /start чтобы начать.")


def phone_handler(update: Update, context: CallbackContext):
    contact = update.message.contact
    user = update.message.from_user
    data_dict = dict((item, getattr(contact, item, None)) for item in ['user_id', 'phone_number',
                                                                       'first_name', 'last_name'])
    last_person = settings.session.query(Person).all()
    current_person = settings.session.query(Person).filter(Person.user_id == data_dict['user_id']).all()
    if not current_person:
        data_dict['user_name'] = user.name
        data_dict['id'] = len(last_person) + 1
        person = Person(**data_dict)
        settings.session.add(person)
        settings.session.commit()
        update.message.reply_text('Ваши данные сохранены!')
    else:
        update.message.reply_text('Ваши данные уже были сохранены!')


def reserve_help(update: Update, context: CallbackContext):
    update.message.reply_text('Для резерва введите в следующем формате:\n'
                              'Резерв {дд.мм.гггг} {чч:мм(c)} {чч:мм(по)} {количество персон}')


def person_s(persons):
    return 'персону' if persons < 2 else 'персоны' if persons in [2, 3] else 'персон'


@get_current_user_for_mh
def reserve_confirm(update: Update, context: CallbackContext, current_person):
    text = update.message.text
    user_data = update.message.from_user
    _, date, time_start, time_end, persons = text.split()
    data = date, time_start, time_end, persons
    persons = int(persons)
    keyboard = [[InlineKeyboardButton('Да', callback_data=f'reserve-true; data-{data}'),
                 InlineKeyboardButton('Нет', callback_data='reserve-false')]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(f'{user_data.full_name}, Вы подверждаете резерв на {date}({time_start}-{time_end}) '
                              f'на {persons} {person_s(persons)}',
                              reply_markup=reply_markup)


@get_current_user_for_qh
def reserve_handler(update: Update, context: CallbackContext, current_person):
    query = update.callback_query
    data = str(query.data)
    data = [item.split('-') for item in data.split('; ')]
    data = dict(data)
    data['reserve'] = data['reserve'] == 'true'
    if data['reserve']:
        data['data'] = eval(data['data'])
        date, time_start, time_end, persons = data['data']
        persons = int(persons)
        data['data'] = {
            'date_start': datetime.strptime(f'{date} {time_start}', '%d.%m.%Y %H:%M'),
            'date_end': datetime.strptime(f'{date} {time_end}', '%d.%m.%Y %H:%M'),
            'persons': persons
        }
        now = datetime.now()
        if data['data']['date_end'] < now or data['data']['date_start'] < now:
            update.callback_query.answer('Один из выбраннного времени находится в прошлом')
        else:
            data['data']['person_id'] = current_person.id
            data['data']['id'] = len(settings.session.query(Reservation).all()) + 1
            reservation = settings.session.query(func.sum(Reservation.persons)). \
                filter(Reservation.date_end >= data['data']['date_start'],
                       Reservation.date_start <= data['data']['date_end'],
                       Reservation.removed == False).one()
            reservation_for_user = settings.session.query(Reservation). \
                filter(Reservation.date_end >= data['data']['date_start'],
                       Reservation.date_start <= data['data']['date_end'],
                       Reservation.removed == False,
                       Reservation.person_id == current_person.id).all()
            if reservation[0] is None or (reservation[0] is not None
                                          and (settings.MAX_SLOTS - reservation[0]) >= persons
                                          and not reservation_for_user):
                new_reservation = Reservation(**data['data'])
                settings.session.add(new_reservation)
                settings.session.commit()
                update.callback_query.answer('Зарезервировали')
            if reservation_for_user:
                update.callback_query.answer('Уже зарезервировали на это время')
            if reservation[0] is not None and (settings.MAX_SLOTS - reservation[0]) < persons:
                update.callback_query.answer('На данное время нет мест, попробуете другой таймслот')
    else:
        update.callback_query.answer('Вы не согласились')


@get_current_user_for_mh
def reservation_list(update: Update, context: CallbackContext, current_person):
    reservation_for_user = get_reservations_for_user(update, context, current_person)
    if reservation_for_user:
        answer = 'Бронирования:\nid | Начало | Окончание | Количество персон\n'
        for item in reservation_for_user:
            data = [item.id,
                    item.date_start.strftime('%d.%m.%Y %H:%M'),
                    item.date_end.strftime('%d.%m.%Y %H:%M'),
                    item.persons]
            data = list(map(str, data))
            answer += ' | '.join(data) + '\n'
        update.message.reply_text(answer)
    else:
        update.message.reply_text('У вас нет активных бронирований')


@get_current_user_for_mh
def delete_reservation_help(update: Update, context: CallbackContext, current_person):
    reservation_for_user = get_reservations_for_user(update, context, current_person)
    if not reservation_for_user:
        update.message.reply_text('У вас нет активных бронирований')
    else:
        update.message.reply_text('Для отмены бронирвания введите: Отмена {id бронирования}\n'
                                  'P.S. id бронирования можно получить в списке бронирований')


@get_current_user_for_mh
def delete_reservation_confirm(update: Update, context: CallbackContext, current_person):
    text = update.message.text
    reservation_id = int(text.split()[1])
    reservation_for_user = settings.session.query(Reservation). \
        filter(Reservation.id == reservation_id,
               Reservation.person_id == current_person.id,
               Reservation.removed == False).all()
    if not reservation_for_user:
        update.message.reply_text('Такого бронирования нет')
    else:
        reservation_for_user = settings.session.query(Reservation). \
            filter(Reservation.id == reservation_id,
                   Reservation.person_id == current_person.id,
                   Reservation.removed == False).one()
        keyboard = [
            [InlineKeyboardButton('Да', callback_data=f'delete_reservation-true; reservation_id-{reservation_id}'),
             InlineKeyboardButton('Нет', callback_data='delete_reservation-false')]]

        reply_markup = InlineKeyboardMarkup(keyboard)
        date = reservation_for_user.date_start
        update.message.reply_text(f'Вы подтверждаете отмену резерва на {date.date().strftime("%d.%m.%Y")} '
                                  f'с {date.time().strftime("%H:%M")} '
                                  f'по {reservation_for_user.date_end.time().strftime("%H:%M")} '
                                  f'на {reservation_for_user.persons} {person_s(reservation_for_user.persons)}',
                                  reply_markup=reply_markup)


@get_current_user_for_qh
def delete_reservation_handler(update: Update, context: CallbackContext, current_person):
    query = update.callback_query
    data = str(query.data)
    data = [item.split('-') for item in data.split('; ')]
    data = dict(data)
    data['delete_reservation'] = data['delete_reservation'] == 'true'
    if data['delete_reservation']:
        reservation_id = data['reservation_id']
        reservation_for_user = settings.session.query(Reservation). \
            filter(Reservation.id == reservation_id,
                   Reservation.person_id == current_person.id,
                   Reservation.removed == False).all()
        if not reservation_for_user:
            query.answer('Такого бронирования нет')
        else:
            settings.session.query(Reservation). \
                filter(Reservation.id == reservation_id,
                       Reservation.person_id == current_person.id,
                       Reservation.removed == False).update({Reservation.removed: True})
            settings.session.commit()
            query.answer('Отменено')
    else:
        query.answer('Вы не согласились')


@get_current_user_for_mh
def delete_all_reservation_confirm(update: Update, context: CallbackContext, current_person):
    reservation_for_user = settings.session.query(Reservation). \
        filter(Reservation.person_id == current_person.id,
               Reservation.removed == False).all()
    if not reservation_for_user:
        update.message.reply_text('Бронирований нет')
    else:
        keyboard = [
            [InlineKeyboardButton('Да', callback_data=f'delete_all_reservation-true'),
             InlineKeyboardButton('Нет', callback_data='delete_all_reservation-false')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Вы подверждаете отмену всех бронирований?', reply_markup=reply_markup)


@get_current_user_for_qh
def delete_all_reservation_handler(update: Update, context: CallbackContext, current_person):
    query = update.callback_query
    data = str(query.data)
    data = [item.split('-') for item in data.split('; ')]
    data = dict(data)
    if data['delete_all_reservation'] == 'true':
        reservation_for_user_query = settings.session.query(Reservation). \
            filter(Reservation.person_id == current_person.id,
                   Reservation.removed == False)
        reservation_for_user = reservation_for_user_query.all()
        if not reservation_for_user:
            update.message.reply_text('Бронирований нет')
        else:
            reservation_for_user_query.update({Reservation.removed: True})
            settings.session.commit()
            query.answer('Отменено')
    else:
        query.answer('Вы не согласились')


def main():
    updater = Updater(settings.BOT_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler(['start', 'restart'], start))
    dp.add_handler(CommandHandler('help', help_command))
    message_handlers = (
        {'filters': Filters.regex('help'), 'callback': help_command},
        {'filters': Filters.contact, 'callback': phone_handler, 'pass_user_data': True},
        {'filters': Filters.regex('Зарезервировать'), 'callback': reserve_help, 'pass_user_data': True},
        {'filters': Filters.regex(r'Резерв \d{2}\.\d{2}\.\d{4} \d{1,2}'), 'callback': reserve_confirm,
         'pass_user_data': True},
        {'filters': Filters.regex('Зарезервировать'), 'callback': reserve_help, 'pass_user_data': True},
        {'filters': Filters.regex('Список бронирований'), 'callback': reservation_list},
        {'filters': Filters.regex('Отменить бронирование'), 'callback': delete_reservation_help},
        {'filters': Filters.regex('Отмена'), 'callback': delete_reservation_confirm},
        {'filters': Filters.regex('Отменить все бронирования'), 'callback': delete_all_reservation_confirm}
    )
    for message_handler in message_handlers:
        dp.add_handler(MessageHandler(**message_handler))
    dp.add_handler(CallbackQueryHandler(reserve_handler,
                                        pattern=r'^reserve',
                                        pass_user_data=True))
    dp.add_handler(CallbackQueryHandler(delete_reservation_handler,
                                        pattern=r'^delete_reservation',
                                        pass_user_data=True))
    dp.add_handler(CallbackQueryHandler(delete_all_reservation_handler,
                                        pattern=r'^delete_all_reservation',
                                        pass_user_data=True))

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()
