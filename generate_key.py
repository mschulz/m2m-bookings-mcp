# generate_key

import os
from binascii import hexlify

print(hexlify(os.urandom(16)))
