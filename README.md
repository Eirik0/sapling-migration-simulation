# Sapling Migration Simulation

This script is intended to simulate strategies for migrating funds from the
Sprout to Sapling shielded pools on the Zcash blockchain.

## How it works

First we generate a mix of mock shielded and transparant transactions up to a
given Sapling activation height. We then continue to generate blocks in a
similar fashion but at the same time for each user/node we execute a stragegy
for migrating Sprout shielded addresses to Sapling shielded addresses.
The script generates a minimal amount of information to execute and validate
the strategy.

As part of execution we write 3 files:
blockvhain.csv:
    This csv file has four columns: "block_height", "input", "output", and
    "amount".
    This file is a simplification of the information stored on the block chain.
    "input" and "output" represent transaction ids and are formatted in a way
    such that we can figure out the type of transaction, and which user the
    amounts belongs to. In the actual Zcash block chain, some of this
    information is obfuscated, but for the sake of the validating the migration
    stragegy in this simulation, it is designed to not hide any infomation.

user_balance_*.csv:
    These csv files have four columns: "user_id", "sprout_balance",
    "sapling_balance", and "transparent_balance".
    These files are intended to provide some insight to the mock data which is
    generated, and to aid in validating the migration stragegy. One file is
    produced before the migration begins, and a second file is produced after
    the simulation ends.

## Usage

After cloning, enter the following command to run the script and generate the
output files:
```
python simulator.py
```
