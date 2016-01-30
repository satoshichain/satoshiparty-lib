"""Variables prefixed with `DEFAULT` should be able to be overridden by
configuration file and command‐line arguments."""

UNIT = 100000000        # The same across assets.


# Versions
VERSION_MAJOR = 9
VERSION_MINOR = 51
VERSION_REVISION = 3
VERSION_STRING = str(VERSION_MAJOR) + '.' + str(VERSION_MINOR) + '.' + str(VERSION_REVISION)


# Shellparty protocol
TXTYPE_FORMAT = '>I'

TWO_WEEKS = 2 * 7 * 24 * 3600
MAX_EXPIRATION = 4 * 2016   # Two months

MEMPOOL_BLOCK_HASH = 'mempool'
MEMPOOL_BLOCK_INDEX = 9999999


# SQLite3
MAX_INT = 2**63 - 1


# Shellcoin Core
OP_RETURN_MAX_SIZE = 40 # bytes


# Currency agnosticism
SCH = 'SCH'
SHP = 'SHP'

SCH_NAME = 'Shellcoin'
SHP_NAME = 'Shellparty'
APP_NAME = SHP_NAME.lower()

DEFAULT_RPC_PORT_TESTNET = 14411
DEFAULT_RPC_PORT = 4411

DEFAULT_BACKEND_PORT_TESTNET = 30135
DEFAULT_BACKEND_PORT = 31100
DEFAULT_BACKEND_PORT_TESTNET_SCHD = 30135
DEFAULT_BACKEND_PORT_SCHD = 31100

UNSPENDABLE_TESTNET = 'mtBurnBurnBurnBurnBurnBurnBurvozW8'
UNSPENDABLE_MAINNET = 'Sburnburnburnburnburnburnburnvhudd'

ADDRESSVERSION_TESTNET = b'\x6f'
PRIVATEKEY_VERSION_TESTNET = b'\xef'
ADDRESSVERSION_MAINNET = b'\x00'
PRIVATEKEY_VERSION_MAINNET = b'\x80'
MAGIC_BYTES_TESTNET = b'\x2a\x2b\x36\x42'   # For bip-0010
MAGIC_BYTES_MAINNET = b'\x3b\x42\x31\x24'   # For bip-0010

BLOCK_FIRST_TESTNET_TESTCOIN = 310000
BURN_START_TESTNET_TESTCOIN = 310000
BURN_END_TESTNET_TESTCOIN = 4017708     # Fifty years, at ten minutes per block.

BLOCK_FIRST_TESTNET = 310000
BLOCK_FIRST_TESTNET_HASH = '000000001f605ec6ee8d2c0d21bf3d3ded0a31ca837acc98893876213828989d'
BURN_START_TESTNET = 310000
BURN_END_TESTNET = 4017708              # Fifty years, at ten minutes per block.

BLOCK_FIRST_MAINNET_TESTCOIN = 278270
BURN_START_MAINNET_TESTCOIN = 278310
BURN_END_MAINNET_TESTCOIN = 2500000     # A long time.

BLOCK_FIRST_MAINNET = 166000
BLOCK_FIRST_MAINNET_HASH = 'df11842a6ab746adf1a078907f1f81ce544fdf09fe42f338e58ac0639c7cae89'
BURN_START_MAINNET = 278310
BURN_END_MAINNET = 283810


# Protocol defaults
# NOTE: If the DUST_SIZE constants are changed, they MUST also be changed in counterblockd/lib/config.py as well
    # TODO: This should be updated, given their new configurability.
# TODO: The dust values should be lowered by 90%, once transactions with smaller outputs start confirming faster: <https://github.com/mastercoin-MSC/spec/issues/192>
DEFAULT_REGULAR_DUST_SIZE = 5430         # TODO: This is just a guess. I got it down to 5530 satoshis.
DEFAULT_MULTISIG_DUST_SIZE = 7800        # <https://SatoshiChaintalk.org/index.php?topic=528023.msg7469941#msg7469941>
DEFAULT_OP_RETURN_VALUE = 0
DEFAULT_FEE_PER_KB = 10000                # Shellcoin Core default is 10000.  # TODO: Lower 10x later, too.


# UI defaults
DEFAULT_FEE_FRACTION_REQUIRED = .009   # 0.90%
DEFAULT_FEE_FRACTION_PROVIDED = .01    # 1.00%


DEFAULT_REQUESTS_TIMEOUT = 20   # 20 seconds
DEFAULT_RPC_BATCH_SIZE = 20     # A 1 MB block can hold about 4200 transactions.

# Custom exit codes
EXITCODE_UPDATE_REQUIRED = 5


DEFAULT_CHECK_ASSET_CONSERVATION = True

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
