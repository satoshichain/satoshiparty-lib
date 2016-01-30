import getpass
import binascii
import logging
logger = logging.getLogger(__name__)
import sys
import json
import time
from decimal import Decimal as D

import bitcoin as SatoshiChainlib
import SatoshiChain.rpc as SatoshiChainlib_rpc
from SatoshiChain.core import CBlock

from shellpartylib.lib import util
from shellpartylib.lib import script
from shellpartylib.lib import config

from shellpartylib.lib.backend import addrindex, shelld

def sortkeypicker(keynames):
    """http://stackoverflow.com/a/1143719"""
    negate = set()
    for i, k in enumerate(keynames):
        if k[:1] == '-':
            keynames[i] = k[1:]
            negate.add(k[1:])
    def getit(adict):
       composite = [adict[k] for k in keynames]
       for i, (k, v) in enumerate(zip(keynames, composite)):
           if k in negate:
               composite[i] = -v
       return composite
    return getit

def BACKEND():
    return sys.modules['shellpartylib.lib.backend.{}'.format(config.BACKEND_NAME)] 

# TODO: Generate this block of code dynamically?

def getblockcount():
    return BACKEND().getblockcount()
def getblockhash(blockcount):
    return BACKEND().getblockhash(blockcount)
def getblock(block_hash):
    block_hex = BACKEND().getblock(block_hash)
    return CBlock.deserialize(util.unhexlify(block_hex))

def searchrawtransactions(address, unconfirmed=False):
    return BACKEND().searchrawtransactions(address, unconfirmed=unconfirmed)
def getrawtransaction(tx_hash, verbose=False):
    return BACKEND().getrawtransaction(tx_hash, verbose=verbose)
def getrawtransaction_batch(txhash_list, verbose=False):
    return BACKEND().getrawtransaction_batch(txhash_list, verbose=verbose)
def sendrawtransaction(tx_hex):
    return BACKEND().sendrawtransaction(tx_hex)

def getrawmempool():
    return BACKEND().getrawmempool()

def extract_addresses(tx_hash):
    return BACKEND().extract_addresses(tx_hash)

def deserialize(tx_hex):
    return SatoshiChainlib.core.CTransaction.deserialize(binascii.unhexlify(tx_hex))
def serialize(ctx):
    return SatoshiChainlib.core.CTransaction.serialize(ctx)


def is_valid(address):
    try:
        script.validate(address)
        return True
    except script.AddressError:
        return False

def get_txhash_list(block):
    return [SatoshiChainlib.core.b2lx(ctx.GetHash()) for ctx in block.vtx]

def input_value_weight(amount):
    # Prefer outputs less than dust size, then bigger is better.
    if amount * config.UNIT <= config.DEFAULT_REGULAR_DUST_SIZE:
        return 0
    else:
        return 1 / amount

def sort_unspent_txouts(unspent, unconfirmed=False):
    # Get deterministic results (for multiAPIConsensus type requirements), sort by timestamp and vout index.
    # (Oldest to newest so the nodes don’t have to be exactly caught up to each other for consensus to be achieved.)
    # searchrawtransactions doesn’t support unconfirmed transactions
    try:
        unspent = sorted(unspent, key=sortkeypicker(['ts', 'vout']))
    except KeyError: # If timestamp isn’t given.
        pass

    # Sort by amount.
    unspent = sorted(unspent, key=lambda x: input_value_weight(x['amount']))

    return unspent

def get_shell_supply(normalize=False):
    """returns the total supply of {} (based on what Shellcoin Core says the current block height is)""".format(config.SCH)
    block_count = getblockcount()
    blocks_remaining = block_count
    total_supply = 0
    reward = 50.0
    while blocks_remaining > 0:
        if blocks_remaining >= 210000:
            blocks_remaining -= 210000
            total_supply += 210000 * reward
            reward /= 2
        else:
            total_supply += (blocks_remaining * reward)
            blocks_remaining = 0
    return total_supply if normalize else int(total_supply * config.UNIT)

def is_scriptpubkey_spendable(scriptpubkey_hex, source, multisig_inputs=False):
    c_scriptpubkey = SatoshiChainlib.core.CScript(SatoshiChainlib.core.x(scriptpubkey_hex))
    vout_address = script.scriptpubkey_to_address(c_scriptpubkey)
    if not vout_address:
        return False

    source = script.make_canonical(source)

    if vout_address == source:
        return True

    return False

class MempoolError(Exception):
    pass

def get_unspent_txouts(source, unconfirmed=False, multisig_inputs=False):
    """returns a list of unspent outputs for a specific address
    @return: A list of dicts, with each entry in the dict having the following keys:
    """
    global MEMPOOL_CACHE_INITIALIZED

    if not MEMPOOL_CACHE_INITIALIZED:
        raise MempoolError('Mempool is not yet ready; please try again in a few minutes.')

    # Get all outputs.
    logger.debug('Getting outputs.')
    if script.is_multisig(source):
        pubkeyhashes = script.pubkeyhash_array(source)
        raw_transactions = searchrawtransactions(pubkeyhashes[1], unconfirmed=True) # unconfirmed=True to prune unconfirmed spent outputs
    else:
        pubkeyhashes = [source]
        raw_transactions = searchrawtransactions(source, unconfirmed=True)

    # Change format.
    # TODO: Slow.
    logger.debug('Formatting outputs.')
    outputs = {}
    for tx in raw_transactions:
        for vout in tx['vout']:
            txid = tx['txid']
            confirmations = tx['confirmations'] if 'confirmations' in tx else 0
            outkey = '{}{}'.format(txid, vout['n']) # edge case: avoid duplicate output
            if outkey not in outputs or outputs[outkey]['confirmations'] < confirmations: 
                coin = {
                        'amount': float(vout['value']),
                        'confirmations': confirmations,
                        'scriptPubKey': vout['scriptPubKey']['hex'],
                        'txid': txid,
                        'vout': vout['n']
                       }
                outputs[outkey] = coin
    outputs = sorted(outputs.values(), key=lambda x: x['confirmations'])

    # Prune unspendable.
    logger.debug('Pruning unspendable outputs.')
    # TODO: Slow.
    outputs = [output for output in outputs if is_scriptpubkey_spendable(output['scriptPubKey'], source)]

    # Prune spent outputs.
    logger.debug('Pruning spent outputs.')
    vins = {(vin['txid'], vin['vout']) for tx in raw_transactions for vin in tx['vin']}
    unspent = []
    for output in outputs:
        if (output['txid'], output['vout']) not in vins:
            unspent.append(output)
    unspent = sorted(unspent, key=lambda x: x['txid'])

    # Remove unconfirmed txouts, if desired.
    if not unconfirmed:
        unspent = [output for output in unspent if output['confirmations'] > 0]
    else:
        # Hackish: Allow only inputs which are either already confirmed or were seen only recently. (Skip outputs from slow‐to‐confirm transanctions.)
        try:
            unspent = [output for output in unspent if output['confirmations'] > 0 or (time.time() - output['ts']) < 6 * 3600] # Cutoff: six hours
        except (KeyError, TypeError):
            pass

    return unspent

class UnknownPubKeyError(Exception):
    pass

def pubkeyhash_to_pubkey(pubkeyhash, provided_pubkeys=None):
    # Search provided pubkeys.
    if provided_pubkeys:
        if type(provided_pubkeys) != list:
            provided_pubkeys = [provided_pubkeys]
        for pubkey in provided_pubkeys:
            if pubkeyhash == script.pubkey_to_pubkeyhash(util.unhexlify(pubkey)):
                return pubkey

    # Search blockchain.
    raw_transactions = searchrawtransactions(pubkeyhash, unconfirmed=True)
    for tx in raw_transactions:
        for vin in tx['vin']:
            scriptsig = vin['scriptSig']
            asm = scriptsig['asm'].split(' ')
            if len(asm) >= 2:
                pubkey = asm[1]
                if pubkeyhash == script.pubkey_to_pubkeyhash(util.unhexlify(pubkey)):
                    return pubkey

    raise UnknownPubKeyError('Public key was neither provided nor published in blockchain.')


def multisig_pubkeyhashes_to_pubkeys(address, provided_pubkeys=None):
    signatures_required, pubkeyhashes, signatures_possible = script.extract_array(address)
    pubkeys = [pubkeyhash_to_pubkey(pubkeyhash, provided_pubkeys) for pubkeyhash in pubkeyhashes]
    return script.construct_array(signatures_required, pubkeys, signatures_possible)


MEMPOOL_CACHE_INITIALIZED = False

def init_mempool_cache():
    global MEMPOOL_CACHE_INITIALIZED

    logger.debug('Initialize mempool cache')
    start = time.time()

    txhash_list = BACKEND().getrawmempool()
    mempool_tx = BACKEND().getrawtransaction_batch(txhash_list, verbose=True)
    vin_txhash_list = []
    for txid in mempool_tx:
        tx = mempool_tx[txid]
        vin_txhash_list += [vin['txid'] for vin in tx['vin']]
    BACKEND().getrawtransaction_batch(vin_txhash_list, verbose=True)

    MEMPOOL_CACHE_INITIALIZED = True
    logger.debug('Mempool cache initialized: {}s for {} transactions'.format(time.time() - start, len(txhash_list) + len(vin_txhash_list)))


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
