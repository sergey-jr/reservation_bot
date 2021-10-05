from enum import Enum


class SuccessMessage(Enum):
    registration = 'Ваши данные сохранены!'
    reserve = 'Зарезервировали'
    delete = 'Отменено'


class ErrorMessage(Enum):
    person = 'Количество персон должно быть строго больше нуля'
    registration = 'Ваши данные уже были сохранены!'
    date = 'Одно из выбраннного времени находится в прошлом'
    reserved_by_user = 'Уже зарезервировали на это время'
    reserve_no_places = 'На данное время нет мест, попробуете другой таймслот'
    reservation_list = 'У вас нет активных бронирований'
    reservation = 'Такого бронирования нет'


class HelpMessage(Enum):
    main = 'Бот для резервирования столиков в ресторане. Используйте /start чтобы начать.'
    reserve = 'Для резерва введите в следующем формате:\n' \
              'Резерв {дд.мм.гггг} {чч:мм(c)} {чч:мм(по)} {количество персон}\n' \
              'Или\n' \
              '{дд.мм.гггг} {чч:мм(c)} {чч:мм(по)} {количество персон}'
    canceled = 'Вы не согласились'
    delete_reservation = 'Для отмены бронирвания введите: Отмена {id бронирования}\n' \
                         'P.S. id бронирования можно получить в списке бронирований'
    reservation_list = 'Бронирования:\nid | Начало | Окончание | Количество персон\n'


class ApproveMessage(Enum):
    reserve = '{full_name}, ' \
              'Вы подверждаете резерв на {date}({time_start}-{time_end}) ' \
              'на {persons} {person_noun}'
    delete_reserve = 'Вы подтверждаете отмену резерва на {date.date().strftime("%d.%m.%Y")} ' \
                     'с {date.time().strftime("%H:%M")} ' \
                     'по {date_end.time().strftime("%H:%M")} ' \
                     'на {persons} {person_noun}'
    delete_all_reserve = 'Вы подверждаете отмену всех бронирований?'
