"""User score service api
"""
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import json
import datetime
import logging
import hashlib
from pyclbr import Class
import re
import uuid
from optparse import OptionParser
from http.server import BaseHTTPRequestHandler, HTTPServer

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class Field:
    """Common field value validation.
    """

    def __init__(self, required, nullable):
        self.required = required
        self.nullable = nullable
        self.empty_field = [[], (), {}, '', None]

    def is_empty(self, inp):
        '''Check if field value is empty.
        '''

        if not inp:
            return True
        return False

    def check_inp(self, inp):
        '''Check if requred value is correct.
        '''

        if self.required and self.is_empty(inp):
            raise ValueError("Поле должно быть заполнено")

        if not self.nullable and inp in self.empty_field:
            raise ValueError("Поле не может быть пустым")


class CharField(Field):
    """Common char field class.
    """

    def check_str_arg(self, inp):
        '''Check is input str.
        '''
        super().check_inp(inp)
        if not isinstance(inp, str):
            raise ValueError("Поле должно содержать текст")
        return inp


class ArgumentsField(Field):
    """User arguments field validation and handling.
    """

    def validate(self, inp):
        '''Field validation.
        '''
        super().check_inp(inp)
        if not isinstance(inp, dict):
            raise ValueError("Поле должно содержать python-словарь")


class EmailField(CharField):
    """E-mail field validation and handling.
    """

    def validate(self, inp):
        '''Field validation.
        '''
        super().check_str_arg(inp)
        email_pattern = '[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+'
        if not re.search(email_pattern, inp):
            raise ValueError('Неверный формат адреса эл. почты')
        return inp


class PhoneField(Field):
    """Phone field validation and handling.
    """

    def validate(self, inp):
        '''Field validation.
        '''
        super().check_inp(inp)
        phone_pattern = '7\d{10}'
        if not re.search(phone_pattern, str(inp)):
            raise ValueError('Неверный формат номера телефона')
        return inp


class DateField(Field):
    """Common date field class.
    """

    def strptime(self, inp):
        '''String to date.
        '''
        default_format = "%d.%m.%Y"
        return datetime.datetime.strptime(inp, default_format).date()

    def validate(self, inp):
        '''Field validation.
        '''
        super().check_inp(inp)
        try:
            return self.strptime(inp)
        except ValueError:
            raise


class BirthDayField(DateField):
    """Birthday field validation and handling.
    """

    def validate(self, inp):
        '''Field validation.
        '''
        inp = super().strptime(inp)
        now = datetime.date.today()
        timedelta = now - inp
        if timedelta.days / 365  > 70:
            raise ValueError("С введенной даты прошло больше 70 лет")
        return inp


class GenderField(Field):
    """Gender field validation and handling.
    """

    def validate(self, inp):
        super().check_inp(inp)
        if inp not in GENDERS:
            raise ValueError("Значение должно быть 0, 1 или 2")
        return inp


class ClientIDsField(Field):
    """ID's field validation and handling.
    """

    def validate_ids(self, inp):
        '''Field validation.
        '''
        super().check_inp(inp)
        if not isinstance(inp, list) \
            or not all(
                        isinstance(elem, int) for elem in inp):
            raise TypeError("Поле должно содержать массив целых чисел")


class ClientsInterestsRequest:
    """Get client IDs and date if validated.
    """

    client_ids = ClientIDsField(required=True, nullable=False)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest:
    """Get person data if validated.
    """

    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    pairs = (bool(first_name and last_name),
             bool(email and phone),
             bool(birthday and gender))

    if not any(pairs):
        raise ValueError('''Некорректно заполнены аргументы.
                            См. требования по заполнению''')


class MethodRequest:
    """Get account and method data if validated.
    """

    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512(datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).hexdigest()
    else:
        digest = hashlib.sha512(request.account + request.login + SALT).hexdigest()
    if digest == request.token:
        return True
    return False


def method_handler(request, ctx, store):
    response, code = None, None
    return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r))
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
