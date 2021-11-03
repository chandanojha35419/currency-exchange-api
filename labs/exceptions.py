import json

from django.db import models, IntegrityError, DatabaseError
from django.http import Http404
from django.urls import Resolver404
from django.utils.encoding import force_text
from rest_framework import status, response, exceptions, views
from rest_framework.utils.serializer_helpers import ReturnDict, ReturnList
from django.utils.translation import ugettext_lazy as _t

__author__ = 'chandanojha'


# -----------------------------------------------
# Reason codes - for detailed explanation of error
#
import settings
import logging

from labs.utils import model_does_not_exists

logger = logging.getLogger(__name__)

class Reason:
    # default codes [1-99] that can reused anywhere
    ACTION_NOT_ALLOWED = 1
    REQUIRED = 2
    NOT_FOUND = 3
    DISABLED = 4
    EXPIRED = 5
    ALREADY_EXISTS = 6
    TYPE_MISMATCH = 7
    MAX_LIMIT = 8
    NOT_IN_RANGE = 9
    VALUE_NOT_ALLOWED = 10

    NEED_OVERRIDE = 98
    NEED_OVERRIDE_REASON = 97

    CLIENT_ERROR = 99  # Incorrect use of API by client

    class Http400:
        USER_EXISTS = 101

    class Http403:
        ACCESS_DENIED = 101
        ACCOUNT_INACTIVE = 102

        STAFF_ONLY = 121
        STAFF_ADMIN_ONLY = 1211
        STAFF_MANAGER_ONLY = 1212
        STAFF_DATA_MANAGER_ONLY = 1213

    class Http404:
        FILE_NOT_FOUND = 101


# -----------------------------------------------
# Custom error classes - adds 'message' and 'reason' to DRF's existing classes
#
# Also uses customized version of force_text_recursive to skip string-conversion of basic data types
#  that can be JSON serialized directly
#
def _force_text_recursive(data):
    """
    Same as drf's _force_text_recursive, but uses 'strings_only=True' to skip non-string fields
    """
    if isinstance(data, list):
        ret = [
            _force_text_recursive(item) for item in data
        ]
        if isinstance(data, ReturnList):
            return ReturnList(ret, serializer=data.serializer)
        return ret
    elif isinstance(data, dict):
        ret = {
            key: _force_text_recursive(value)
            for key, value in data.items()
        }
        if isinstance(data, ReturnDict):
            return ReturnDict(ret, serializer=data.serializer)
        return ret
    return force_text(data, strings_only=True)


class ErrorMixin:
    """
    Adds 'message' and 'reason' to DRF's existing error classes
    """
    default_detail = _t("Something went wrong. Please try after sometime.")

    def __init__(self, message=None, detail=None, reason=None):

        if detail:
            # don't add an extra 'detail' level if its already there, could happen if we are passed
            # DRF's exception object as detail
            if hasattr(detail, 'detail'):
                detail = detail.detail
            elif isinstance(detail, dict):
                # Or when we are given 'detail' dict further containing 'message' and detail' as key
                if not message and 'message' in detail:
                    message = detail.pop('message')
                if 'detail' in detail:
                    detail = detail['detail']

            # see if detail is json serializable
            try:
                json.loads(detail)
            except:
                # Not a json object, lets serialize it ourselves
                detail = _force_text_recursive(detail)

        self.detail = detail
        self.message = _force_text_recursive(message or self.default_detail)
        self.reason = reason

    def __str__(self):
        return str(self._response_data())

    def _response_data(self):
        res = {'code': self.status_code, 'message': self.message}

        if self.reason:
            res['reason'] = self.reason

        if self.detail:
            res['detail'] = self.detail

        return res

    def response(self, logger=None):
        """
        Http response object for this exception
        :param logger: logs the error using this logger if provided
        :return: Http response object that can be returned to client
        """
        data = self._response_data()
        if logger:
            logger(data)

        # Suppress extra details to be sent to client in case of infamous 'Internal Server Error'. It might
        # leak sensitive information
        # Let it go for non-live environments
        if self.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR and settings.DEBUG==False:
            if 'detail' in data:
                del data['detail']

        # By default Django will log all 4xx as Warnings and 5xx as errors... even if we have already done it!
        #
        # So signal it not to do that if we have already logged the exception, or
        # if it is 400 (could be too much of them because of user input validations)
        r = response.Response(data=data, status=self.status_code)
        r._has_been_logged = bool(logger) or (self.status_code > status.HTTP_400_BAD_REQUEST)
        return r


class ValidationError(ErrorMixin, exceptions.APIException):
    """
    Sub-classed from exceptions.APIException instead of exceptions.ValidationError as DRF's code
    are doing some special handling of their ValidationError ('details' required, plus losing
    our message & reason fields in the process) which we want to skip
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _t("Your request could not be processed.")


class AuthenticationError(ErrorMixin, exceptions.AuthenticationFailed):
    default_detail = _t('Incorrect authentication credentials.')


class Forbidden(ErrorMixin, exceptions.PermissionDenied):
    default_detail = _t('You do not have permission to perform this action.')


class NotFound(ErrorMixin, exceptions.NotFound):
    default_detail = _t("The resource you requested was not found.")


class MethodNotAllowed(ErrorMixin, exceptions.MethodNotAllowed):
    default_detail = _t("Method not available. Please never try again :)")


class ServiceUnavailable(ErrorMixin, exceptions.APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = _t("Service is currently not available. Please try after sometime.")


class ServerError(ErrorMixin, exceptions.APIException):
    pass


class ClientError(ServerError):
    default_detail = _t(
        "Unexpected request from client. May be the application is being accessed in multiple tabs/browsers?")

    def __init__(self, message=None, detail=None, reason=None):
        super().__init__(message, detail=detail, reason=reason or Reason.CLIENT_ERROR)


def url_not_found(exception):
    assert isinstance(exception, Resolver404)

    message = _t('URL you requested was not found')
    try:
        return NotFound(message=message, detail=exception.args[0]['path']).response()
    except:
        return NotFound(message=message).response()


def friendly_integrity_error(e):
    """
    Integrity error returned from underlying DB results in 500 at client with not-so-friendly message
    Map it to ValidationError with better message

    :param e: IntegrityError
    :return: ValidationError
    """
    args = getattr(e, 'args', None)
    if args and args[0] == 1062 and len(args) > 1:  # Duplicate Entry
        msg = args[1]
        if msg.startswith('Duplicate') and ' for key' in msg:
            return ValidationError(msg.split(' for key')[0], detail=e)
        return ValidationError('Duplicate entry', detail=e)
    return bot_error(e)


def bot_error(error, bot_error_class=None):
    """
    Our custom error from built-in errors. Tries to guess the error class to be used if not provided by caller

    :param error: Any built-in errors to be converted to our custom error object
    :param bot_error_class: Our custom error class to be used - Optional
    :return: BOT error object
    """

    if isinstance(error, ErrorMixin):
        return error  # It is already our custom error object, no conversion needed

    if not bot_error_class:
        # Try to guess the bot_error_class from error object class if not provided
        error_class = type(error)

        if error_class == exceptions.ValidationError:
            bot_error_class = ValidationError
        elif error_class in (exceptions.AuthenticationFailed, exceptions.NotAuthenticated):
            bot_error_class = AuthenticationError
        elif error_class in (exceptions.PermissionDenied, models.ProtectedError):
            bot_error_class = Forbidden
        elif error_class == exceptions.NotFound:
            bot_error_class = NotFound
        elif error_class == exceptions.MethodNotAllowed:
            bot_error_class = MethodNotAllowed
        elif error_class == IntegrityError:
            bot_error_class = ValidationError
        elif error_class == DatabaseError:
            bot_error_class = ServiceUnavailable
        else:
            bot_error_class = ServerError

    detail = getattr(error, 'detail', None) or error.args or error
    return bot_error_class(detail=detail)


def success_response(message, detail=None, code=status.HTTP_200_OK):
    """
    Wrapper for quickly creating success response

    :param message: success message to be passed to client
    :param detail: any extra details if any
    :param code: success code (2xx series)
    :return: Http Response object
    """
    message = message or 'Success'
    res = {'code': code, 'message': message}
    if detail:
        res['detail'] = detail
    return response.Response(res, status=code)


class ErrorResponse(Exception):
    """ Wraps a response.Response() object that can be thrown all the way up to the caller """

    def __init__(self, data=None, status=None, **kwargs):
        self._response = response.Response(data, status, **kwargs)

    def __str__(self):
        return str(self.response)

    def response(self, logger=None):
        """
        Http response object for this exception
        :param logger: logs the error using this logger if provided
        :return: Http response object that can be returned to client
        """
        if logger:
            logger(self._response.data)
        return self._response


def exception_handler(exc, context):
    """
    We want to handle our exceptions ourselves, the default drf's implementation drop everything but 'detail'
     which in our case is actually optional
    """
    if isinstance(exc, ErrorMixin):
        return exc.response()
    elif isinstance(exc, exceptions.APIException):
        return bot_error(exc).response()

    return views.exception_handler(exc, context)


def view_exception_handler(view_method):
    def decorator(self, request, *args, **kwargs):
        try:
            return view_method(self, request, *args, **kwargs)
        except (ValidationError, AuthenticationError, NotFound, Forbidden, ServiceUnavailable, ServerError) as e:
            return e.response(logger=logger.info)
        except exceptions.ValidationError as e:
            return bot_error(e, ValidationError).response(logger=logger.info)
        except exceptions.NotFound as e:
            return bot_error(e, NotFound).response(logger=logger.info)
        except exceptions.PermissionDenied as e:
            return bot_error(e, Forbidden).response(logger=logger.warn)
        except exceptions.APIException as e:
            return bot_error(e, ServerError).response(logger=logger.exception)

        except model_does_not_exists(self) as e:
            return NotFound(detail=e).response(logger=logger.warn)
        except Http404 as e:
            return NotFound(detail=e).response(logger=logger.info)

        except IntegrityError as e:
            return friendly_integrity_error(e).response(logger.warn)

        except Exception as e:
            return bot_error(e).response(logger=logger.exception)

    return decorator