import xlsxwriter
import os
import datetime
import pytz


def plan_request(message):
    request = message.text.split()
    if len(request) != 2 or request[0].lower() != 'план':
        return False
    else:
        try:
            int(request[1])
        except ValueError:
            return False
        else:
            return True


def earned_request(message):
    request = message.text.split()
    if len(request) != 1:
        return False
    else:
        try:
            int(request[0])
        except ValueError:
            return False
        else:
            return True


def stat_mes_request(message):
    request = message.text.split()
    options1 = ['стат', 'статистика']
    options2 = ['день', 'неделя', 'нед']
    if len(request) != 2 or request[0].lower() not in options1:
        return False
    else:
        if request[1].lower() in options2:
            return True
        else:
            return False


def stat_file_request(message):
    request = message.text.split()
    options1 = ['стат', 'статистика']
    options2 = ['месяц', 'мес', 'год', 'всё', 'все', 'вся']
    if len(request) != 2 or request[0].lower() not in options1:
        return False
    else:
        if request[1].lower() in options2:
            return True
        else:
            return False


def delete_call_request(call):
    if call.data == 'delete' or call.data == 'abort':
        return True
    else:
        return False


def stats_to_file(data):
    tz = pytz.timezone('Etc/GMT-7')
    time = datetime.datetime.now(tz=tz).strftime('%Y%m%d%H%M%S')
    file_name = f"Stat_{time}.xlsx"
    workbook = xlsxwriter.Workbook(file_name, {'constant_memory': True})
    worksheet = workbook.add_worksheet('Stats')
    worksheet.set_column('B:E', 15)

    mane_format = workbook.add_format({'align': 'center'})
    num_format = workbook.add_format({'num_format': '0', 'align': 'center'})
    bold = workbook.add_format({'bold': True, 'align': 'center'})

    col_names = ['№', 'Дата', 'План', 'Заработано', 'Выполнено (%)']
    col_id = 0
    for name in col_names:
        worksheet.write(0, col_id, name, bold)
        col_id += 1

    formats = [num_format, mane_format, num_format, num_format]
    row_id = 1
    for row in data:
        col_id = 0
        for value in row:
            worksheet.write(row_id, col_id, value, formats[col_id])
            col_id += 1
        percent = 100 if row[2] == 0 else round((row[3] / row[2]) * 100, 2)
        worksheet.write(row_id, col_id, percent, mane_format)
        row_id += 1
    workbook.close()
    return file_name


def remove_stat_file(file_name):
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), file_name)
    os.remove(path)
