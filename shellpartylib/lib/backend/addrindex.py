import logging
logger = logging.getLogger(__name__)
import sys
import json
import requests
from requests.exceptions import Timeout, ReadTimeout, ConnectionError
import time
import threading
from functools import lru_cache

from shellpartylib.lib import script
from shellpartylib.lib import config

SatoshiChain_rpc_session = None

class BackendRPCError(Exception):
    pass

def rpc_call(payload):
    url = config.BACKEND_URL
    headers = {'content-type': 'application/json'}

    global SatoshiChain_rpc_session
    if not SatoshiChain_rpc_session:
        SatoshiChain_rpc_session = requests.Session()
    response = None
    TRIES = 12
    for i in range(TRIES):
        try:
            response = SatoshiChain_rpc_session.post(url, data=json.dumps(payload), headers=headers, verify=(not config.BACKEND_SSL_NO_VERIFY), timeout=config.REQUESTS_TIMEOUT)
            if i > 0:
                logger.debug('Successfully connected.')
            break
        except (Timeout, ReadTimeout, ConnectionError):
            logger.debug('Could not connect to backend at `{}`. (Try {}/{})'.format(url, i+1, TRIES))
            time.sleep(5)

    if response == None:
        if config.TESTNET:
            network = 'testnet'
        else:
            network = 'mainnet'
        raise BackendRPCError('Cannot communicate with backend at `{}`. (server is set to run on {}, is backend?)'.format(url, network))
    elif response.status_code not in (200, 500):
        raise BackendRPCError(str(response.status_code) + ' ' + response.reason)

    # Return result, with error handling.
    response_json = response.json()
    # Batch query returns a list
    if isinstance(response_json, list):
        return response_json
    if 'error' not in response_json.keys() or response_json['error'] == None:
        return response_json['result']
    elif response_json['error']['code'] == -5:   # RPC_INVALID_ADDRESS_OR_KEY
        raise BackendRPCError('{} Is `txindex` enabled in {} Core?'.format(response_json['error'], config.SCH_NAME))
    elif response_json['error']['code'] in [-28, -8, -2]:  
        # “Verifying blocks...” or “Block height out of range” or “The network does not appear to fully agree!“ 
        logger.debug('Backend not ready. Sleeping for ten seconds.')
        # If Shellcoin Core takes more than `sys.getrecursionlimit() * 10 = 9970`
        # seconds to start, this’ll hit the maximum recursion depth limit.
        time.sleep(10)
        return rpc_call(payload)
    else:
        raise BackendRPCError('{}'.format(response_json['error']))

def rpc(method, params):
    payload = {
        "method": method,
        "params": params,
        "jsonrpc": "2.0",
        "id": 0,
    }
    return rpc_call(payload)
    
def rpc_batch(payload):

    def get_chunks(l, n):
        n = max(1, n)
        return [l[i:i + n] for i in range(0, len(l), n)]

    chunks = get_chunks(payload, config.RPC_BATCH_SIZE)
    responses = []
    for chunk in chunks:
        responses += rpc_call(chunk)
    return responses

# TODO: use scriptpubkey_to_address()
@lru_cache(maxsize=4096)
def extract_addresses(tx_hash):
    logger.debug('Extract addresses: {}'.format(tx_hash))
    # TODO: Use `rpc._batch` here.
    tx = getrawtransaction(tx_hash, verbose=True)
    addresses = []

    for vout in tx['vout']:
        if 'addresses' in vout['scriptPubKey']:
            addresses += vout['scriptPubKey']['addresses']

    txhash_list = [vin['txid'] for vin in tx['vin']]
    raw_transactions = getrawtransaction_batch(txhash_list, verbose=True)
    for vin in tx['vin']:
        vin_tx = raw_transactions[vin['txid']]
        vout = vin_tx['vout'][vin['vout']]
        if 'addresses' in vout['scriptPubKey']:
            addresses += vout['scriptPubKey']['addresses']

    return addresses, tx

def unconfirmed_transactions(address):
    # NOTE: This operation can be very slow.
    logger.debug('Checking mempool for UTXOs.')

    unconfirmed_tx = []
    mempool = getrawmempool()
    for index, tx_hash in enumerate(mempool):
        logger.debug('Possible mempool UTXO: {} ({}/{})'.format(tx_hash, index, len(mempool)))
        addresses, tx = extract_addresses(tx_hash)
        if address in addresses:
            unconfirmed_tx.append(tx)
    return unconfirmed_tx

def searchrawtransactions(address, unconfirmed=False):

    # Get unconfirmed transactions.
    if unconfirmed:
        logger.debug('Getting unconfirmed transactions.')
        unconfirmed = unconfirmed_transactions(address)
    else:
        unconfirmed = []

    # Get confirmed transactions.
    try:
        logger.debug('Searching raw transactions.')
        rawtransactions = rpc('searchrawtransactions', [address, 1, 0, 9999999])
    except BackendRPCError as e:
        if str(e) == '404 Not Found':
            raise BackendRPCError('Unknown RPC command: `searchrawtransactions`. Please use a version of {} Core which supports an address index.'.format(config.SCH_NAME))
        else:
            raise BackendRPCError(str(e))
    confirmed = [tx for tx in rawtransactions if tx['confirmations'] > 0]

    return unconfirmed + confirmed

def getblockcount():
    return rpc('getblockcount', [])

def getblockhash(blockcount):
    return rpc('getblockhash', [blockcount])

def getblock(block_hash):
    return rpc('getblock', [block_hash, False])

def getrawtransaction(tx_hash, verbose=False):
    return getrawtransaction_batch([tx_hash], verbose=verbose)[tx_hash]

def getrawmempool():
    return rpc('getrawmempool', [])

def sendrawtransaction(tx_hex):
    return rpc('sendrawtransaction', [tx_hex])

# TODO: move to __init__.py
RAW_TRANSACTIONS_CACHE = {}
RAW_TRANSACTIONS_CACHE_KEYS = []
RAW_TRANSACTIONS_CACHE_SIZE = 10000
raw_transaction_cache_lock = threading.Lock()

def getrawtransaction_batch(txhash_list, verbose=False):
    with raw_transaction_cache_lock:
        tx_hash_call_id = {}
        call_id = 0
        payload = []
        # payload for transactions not in cache
        for tx_hash in txhash_list:
            if tx_hash not in RAW_TRANSACTIONS_CACHE:
                payload.append({
                    "method": 'getrawtransaction',
                    "params": [tx_hash, 1],
                    "jsonrpc": "2.0",
                    "id": call_id
                })
                tx_hash_call_id[call_id] = tx_hash
                call_id += 1

        # populate cache
        if len(payload) > 0:
            batch_responses = rpc_batch(payload)
            for response in batch_responses:
                if 'error' not in response or response['error'] is None:
                    tx_hex = response['result']
                    tx_hash = tx_hash_call_id[response['id']]
                    if tx_hash not in RAW_TRANSACTIONS_CACHE:
                        RAW_TRANSACTIONS_CACHE[tx_hash] = tx_hex
                        RAW_TRANSACTIONS_CACHE_KEYS.append(tx_hash)
                else:
                    raise BackendRPCError('{}'.format(response['error']))

        # get transactions from cache
        result = {}
        for tx_hash in txhash_list:
            if verbose:
                result[tx_hash] = RAW_TRANSACTIONS_CACHE[tx_hash]
            else:
                result[tx_hash] = RAW_TRANSACTIONS_CACHE[tx_hash]['hex']

        # remove oldest hashes from cache
        while len(RAW_TRANSACTIONS_CACHE_KEYS) > RAW_TRANSACTIONS_CACHE_SIZE:
            first_hash = RAW_TRANSACTIONS_CACHE_KEYS[0]
            del(RAW_TRANSACTIONS_CACHE[first_hash])
            RAW_TRANSACTIONS_CACHE_KEYS.pop(0) 

        return result

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
