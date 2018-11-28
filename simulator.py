#!/usr/bin/env python2

import random


NUM_BLOCKS = 400
ZEC_PER_BLOCK = 10
SHIELDED_ODDS = 0.2  # Assume 20% of txs are shielded

# TODO Add tiers of users
NUM_USERS = 10


# TODO: consider tx type ?
class Transaction:
    def __init__(self, block_height, input, output, amount):
        self.block_height = block_height
        # tx_id = ("s|t" + user_id + "_" + tx_num) or ("cb_" + cb_index)
        self.input = input
        self.output = output
        self.amount = amount


class User:
    def __init__(self, user_id):
        self.user_id = user_id
        self.shielded_amounts = []
        self.transparent_amounts = []
        self.num_txs = 0

    def add_amount(self, is_shielded, amount):
        if is_shielded:
            tx_id = "s" + str(self.user_id) + "_" + str(len(self.shielded_amounts))
            self.shielded_amounts.append(amount)
        else:
            tx_id = "t" + str(self.user_id) + "_" + str(len(self.transparent_amounts))
            self.transparent_amounts.append(amount)
        return tx_id


def main():
    # Generate some users
    users = []
    for user_id in xrange(0, NUM_USERS):
        users.append(User(user_id))

    transactions = []
    # Generate block data
    for block_height in xrange(1, NUM_BLOCKS):
        # Distribute coinbase
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
            tx_id = user.add_amount(is_shielded, distibution_amount)

            # Append tx to list
            transactions.append(Transaction(block_height, "cb_" + str(cb_index), tx_id, distibution_amount))

            coinbase_amount -= distibution_amount
            cb_index += 1

    blockchain_file = open("blockchain.csv", "w+")
    blockchain_file.write("block_height,input,output,amount\n")

    for tx in transactions:
        blockchain_file.write("{},{},{},{}\n".format(tx.block_height, tx.input, tx.output, tx.amount))

    blockchain_file.flush()
    blockchain_file.close()


if __name__ == '__main__':
    main()
