import logging, sys

#logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

email = 'inactivebiancamgrenville##$$##gmail.cominactive'

from validate_email import validate_email
if validate_email(email, check_mx=True, debug=False, use_blacklist=False):
    print('Valid')
else:
    print('Invalid')
