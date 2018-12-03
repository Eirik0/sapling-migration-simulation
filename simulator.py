#!/usr/bin/env python2

from decimal import Decimal
from enum import Enum
import random

SAPLING_ACTIVATION_HEIGHT = 400
SIMULATION_END_HEIGHT = 600

ZATOSHIS_PER_ZEC = 100000000
ZATOSHIS_PER_BLOCK = 10 * ZATOSHIS_PER_ZEC
MIN_COINBASE_DISTRIBUTION = ZATOSHIS_PER_ZEC // 20

SHIELDED_PROBABILITY = 0.2  # Assume 20% of coinbase txs are shielded

# TODO Add tiers of users
NUM_USERS = 10


class TxType(Enum):
    transparent = 't'
    sprout = 'x'
    sapling = 'z'


class TxInput(object):
    def __init__(self, tx_type, prev_txid, prev_index):
        self.tx_type = tx_type
        self.prev_txid = prev_txid
        self.prev_index = prev_index

    def __str__(self):
        return "{{\"tx_type\":\'{}\',\"prev_tx\":{},\"prev_index\":{}}}".format(self.tx_type.value, self.prev_txid, self.prev_index)


class TxOutput(object):
    def __init__(self, tx_type, index, amount):
        assert(amount > 0)
        self.tx_type = tx_type
        self.index = index
        self.amount = amount
        self.spent = False

    def __str__(self):
        return "{{\"tx_type\":\'{}\',\"index\":{},\"amount\":{},\"spent\":{}}}".format(self.tx_type.value, self.index, self.amount, self.spent)


class Transaction(object):
    # A map from txid to transaction
    tx_map = dict()
    # Used to calculate a unique txid
    next_txid = 0

    def __init__(self, inputs, outputs):
        self.txid = Transaction.get_next_txid()
        self.inputs = inputs
        self.outputs = outputs

        Transaction.tx_map[self.txid] = self

        # Check total_in == total_out for non-coinbase transactions
        if len(inputs) > 0:
            global tx_map

            total_in = 0
            for input in inputs:
                prevout = Transaction.tx_map[input.prev_txid].get_prevout(input)
                assert(not prevout.spent)
                prevout.spent = True
                total_in += prevout.amount

            total_out = 0
            for output in outputs:
                total_out += output.amount

            assert(total_in == total_out)

    def get_prevout(self, input):
        for output in self.outputs:
            if output.tx_type == input.tx_type and output.index == input.prev_index:
                return output

        raise Exception('Prevout not found')

    @staticmethod
    def get_next_txid():
        txid = Transaction.next_txid
        Transaction.next_txid += 1
        return txid


class User(object):
    def __init__(self, user_id):
        self.user_id = user_id
        self.outputs = []  # This is a pair of (Transaction.txid, TxOutput)

    def get_balance(self, tx_type):
        balance = 0
        for txid, output in self.outputs:
            if output.tx_type == tx_type and not output.spent:
                balance += output.amount
        return balance

    def add_output(self, txid, output):
        self.outputs.append((txid, output))


class UserMigrationStrategy(object):
    def migrate_funds(self, user, block_height):
        return []


class UniformRandomDistributionStrategy(UserMigrationStrategy):
    def __init__(self, lowerbound, upperbound):
        self.lowerbound = lowerbound
        self.upperbound = upperbound

    def migrate_funds(self, user, block_height):
        target_amount = random.randint(self.lowerbound, self.upperbound)
        actual_amount = 0
        inputs = []
        # TODO: sort amounts?
        for txid, output in user.outputs:
            if not output.spent and output.tx_type == TxType.sprout:
                inputs.append(TxInput(output.tx_type, txid, output.index))
                actual_amount += output.amount
                if actual_amount >= target_amount:
                    break

        if len(inputs) == 0:
            return []

        out_amount = min(target_amount, actual_amount)
        outputs = [TxOutput(TxType.sapling, 0, out_amount)]
        if actual_amount > target_amount:
            outputs.append(TxOutput(TxType.sprout, 1, actual_amount - target_amount))

        tx = Transaction(inputs, outputs)

        for output in outputs:
            user.add_output(tx.txid, output)

        return [tx]


def distribute_coinbase_transactions(users, is_sapling):
    outputs = []
    out_index = 0
    coinbase_amount = ZATOSHIS_PER_BLOCK
    while coinbase_amount > 0:
        # Distribute random amount to random user
        if coinbase_amount > MIN_COINBASE_DISTRIBUTION:
            distibution_amount = random.randint(0, coinbase_amount)
        else:
            distibution_amount = coinbase_amount

        is_shielded = random.uniform(0, 1) <= SHIELDED_PROBABILITY
        tx_type = (TxType.sapling if is_sapling else TxType.sprout) if is_shielded else TxType.transparent

        outputs.append(TxOutput(tx_type, out_index, distibution_amount))

        coinbase_amount -= distibution_amount
        out_index += 1

    tx = Transaction([], outputs)

    for output in outputs:
        user = users[random.randint(0, NUM_USERS - 1)]
        user.add_output(tx.txid, output)

    return tx


def write_user_balance_file(users, is_sapling):
    if is_sapling:
        sorted_users = sorted(users, key=lambda user: user.get_balance(TxType.sapling), reverse=True)
        user_balance_file_name = "user_balance_sapling.csv"
    else:
        sorted_users = sorted(users, key=lambda user: user.get_balance(TxType.sprout), reverse=True)
        user_balance_file_name = "user_balance_sprout.csv"

    user_balance_file = open(user_balance_file_name, "w+")
    user_balance_file.write("user_id,sprout_balance,sapling_balance,transparent_balance\n")

    total_sprout = 0
    total_sapling = 0
    total_transparent = 0

    for user in sorted_users:
        sprout = user.get_balance(TxType.sprout)
        sapling = user.get_balance(TxType.sapling)
        transparent = user.get_balance(TxType.transparent)

        user_balance_file.write("{},{},{},{}\n".format(
            user.user_id,
            Decimal(sprout) / ZATOSHIS_PER_ZEC,
            Decimal(sapling) / ZATOSHIS_PER_ZEC,
            Decimal(transparent) / ZATOSHIS_PER_ZEC
        ))

        total_sprout += sprout
        total_sapling += sapling
        total_transparent += transparent

    user_balance_file.write("{},{},{},{}\n".format(
        "total",
        Decimal(total_sprout) / ZATOSHIS_PER_ZEC,
        Decimal(total_sapling) / ZATOSHIS_PER_ZEC,
        Decimal(total_transparent) / ZATOSHIS_PER_ZEC
    ))

    user_balance_file.write("grand_total:{}\n".format(Decimal(total_sprout+total_sapling+total_transparent) / ZATOSHIS_PER_ZEC))

    user_balance_file.flush()
    user_balance_file.close()


def main():
    # Generate some users
    users = []
    for user_id in xrange(0, NUM_USERS):
        users.append(User(user_id))

    block_chain = []

    # Generate Sprout block data
    for block_height in xrange(0, SAPLING_ACTIVATION_HEIGHT):
        cb_tx = distribute_coinbase_transactions(users, False)
        block_chain.append([cb_tx])

    write_user_balance_file(users, False)

    strategy = UniformRandomDistributionStrategy(ZATOSHIS_PER_ZEC, 10 * ZATOSHIS_PER_ZEC)  # Try to migrate 1 - 10 zec

    # Generate Sapling block data
    for block_height in xrange(SAPLING_ACTIVATION_HEIGHT, SIMULATION_END_HEIGHT):
        cb_tx = distribute_coinbase_transactions(users, True)
        block_txs = [cb_tx]
        for user in users:
            for tx in strategy.migrate_funds(user, block_chain):
                block_txs.append(tx)
        block_chain.append(block_txs)

    write_user_balance_file(users, True)

    blockchain_file = open("blockchain.csv", "w+")
    blockchain_file.write("block_height,txid,inputs,outputs\n")

    for block_height, txs in enumerate(block_chain):
        for tx in txs:
            blockchain_file.write("{},{},{},{}\n".format(
                block_height,
                tx.txid,
                "[{}]".format(','.join(str(i) for i in tx.inputs)),
                "[{}]".format(','.join(str(o) for o in tx.outputs))
            ))

    blockchain_file.flush()
    blockchain_file.close()


if __name__ == '__main__':
    main()
