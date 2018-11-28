#!/usr/bin/env python2

import random


SAPLING_ACTIVATION_HEIGHT = 400
SIMULATION_END_HEIGHT = 600
ZEC_PER_BLOCK = 10
SHIELDED_ODDS = 0.2  # Assume 20% of txs are shielded

# TODO Add tiers of users
NUM_USERS = 10

SPROUT_PREXIX = "x"
SAPLING_PREFIX = "z"
TRANSPARENT_PREFIX = "t"


class Transaction:
    def __init__(self, block_height, input, output, amount):
        self.block_height = block_height
        # tx_id = (PREFIX + "_" + user_id + "_" + tx_num) or ("cb_" + cb_index)
        self.input = input
        self.output = output
        self.amount = amount


class User:
    def __init__(self, user_id):
        self.user_id = user_id
        self.sprout_amounts = []
        self.sapling_amounts = []
        self.transparent_amounts = []
        self.num_txs = 0

    def add_amount(self, is_shielded, amount, is_sapling):
        if is_shielded:
            if is_sapling:
                tx_id = SAPLING_PREFIX + str(self.user_id) + "_" + str(len(self.sapling_amounts))
                self.sapling_amounts.append(amount)
            else:
                tx_id = SPROUT_PREXIX + str(self.user_id) + "_" + str(len(self.sprout_amounts))
                self.sprout_amounts.append(amount)
        else:
            tx_id = TRANSPARENT_PREFIX + str(self.user_id) + "_" + str(len(self.transparent_amounts))
            self.transparent_amounts.append(amount)
        return tx_id


def distribute_coinbase_transactions(block_height, users, transactions, is_sapling):
    coinbase_amount = ZEC_PER_BLOCK
    cb_index = 0
    while coinbase_amount > 0:
        # Distriburte random amount to random user
        if coinbase_amount > 0.5:
            distibution_amount = random.uniform(0, coinbase_amount)
        else:
            distibution_amount = coinbase_amount

        user = users[random.randint(0, NUM_USERS - 1)]
        is_shielded = random.uniform(0, 1) <= SHIELDED_ODDS
        tx_id = user.add_amount(is_shielded, distibution_amount, is_sapling)

        # Append tx to list
        transactions.append(Transaction(block_height, "cb_" + str(cb_index), tx_id, distibution_amount))

        coinbase_amount -= distibution_amount
        cb_index += 1


def write_user_balance_file(users, before_sapling_activation):
    if before_sapling_activation:
        sorted_users = sorted(users, key=lambda user: sum(user.sprout_amounts), reverse=True)
        user_balance_file_name = "user_balance_sprout.csv"
    else:
        sorted_users = sorted(users, key=lambda user: sum(user.sapling_amounts), reverse=True)
        user_balance_file_name = "user_balance_sapling.csv"

    user_balance_file = open(user_balance_file_name, "w+")
    user_balance_file.write("user_id,sprout_balance,sapling_balance,transparent_balance\n")

    for user in sorted_users:
        user_balance_file.write("{},{},{},{}\n".format(user.user_id, sum(user.sprout_amounts), sum(user.sapling_amounts), sum(user.transparent_amounts)))

    user_balance_file.flush()
    user_balance_file.close()


def main():
    # Generate some users
    users = []
    for user_id in xrange(0, NUM_USERS):
        users.append(User(user_id))

    transactions = []

    # Generate Sprout block data
    for block_height in xrange(1, SAPLING_ACTIVATION_HEIGHT):
        distribute_coinbase_transactions(block_height, users, transactions, False)

    write_user_balance_file(users, True)

    # Generate Sapling block data
    for block_height in xrange(SAPLING_ACTIVATION_HEIGHT, SIMULATION_END_HEIGHT):
        distribute_coinbase_transactions(block_height, users, transactions, True)

    write_user_balance_file(users, False)

    blockchain_file = open("blockchain.csv", "w+")
    blockchain_file.write("block_height,input,output,amount\n")

    for tx in transactions:
        blockchain_file.write("{},{},{},{}\n".format(tx.block_height, tx.input, tx.output, tx.amount))

    blockchain_file.flush()
    blockchain_file.close()


if __name__ == '__main__':
    main()
