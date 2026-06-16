import traceback
from django.http import UnreadablePostError

def skip_ioerror_post(record):
    """
    Filter out IOError (raised when a user looses connection) from the admin emails
    """
    if record.exc_info:
        exc_type, exc_value = record.exc_info[:2]
        if isinstance(exc_value, UnreadablePostError):
            return False
        if isinstance(exc_value, IOError):
            # WARNING Do not assign record.exc_info[2] (traceback) to a local variable!
            # https://docs.python.org/2/library/sys.html , refer to sys.exc_info()
            for filename, line_number, function_name, text in traceback.extract_tb(
                record.exc_info[2]
                ):
                if function_name in ('parse_file_upload', '_perform_form_overloading',):
                    return False
    return True

