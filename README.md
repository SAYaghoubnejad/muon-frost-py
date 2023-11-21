# Muon FROST
This is the Python implementation of the FROST (Flexible Round-Optimized Schnorr Threshold) algorithm for the Muon network.

FROST is a cryptographic algorithm designed for threshold signature schemes. It provides enhanced security and efficiency for decentralized systems by allowing a subset of a group to sign messages on behalf of the entire group. FROST's round-optimized design reduces the number of communication rounds required for generating a signature, making it more efficient than traditional threshold signature schemes.

## Benefits of FROST
- **Efficiency:** Reduces the number of rounds in the signing process, enhancing speed and efficiency in distributed environments.
- **Scalability:** Adaptable to various group sizes, making it ideal for large, decentralized networks.

## How to Setup

To create a virtual environment (`venv`) and install the required packages, run the following commands:

```bash
$ git clone https://github.com/SAYaghoubnejad/muon-frost-py.git --recurse-submodules
$ cd muon-frost-py
$ virtualenv -p python3.10 venv
$ source venv/bin/activate
(venv) $ pip install -r requirements.txt
```

**Note:** The required Python version is `3.10`.

## How to Run

To run the project, first open `m` additional terminals for `m` nodes and activate the `venv` in these terminals. Note that `m` is an arbitrary positive number. Then change the directory to the `muon-frost-py` project root and run the following command in each terminal to configure the root path of the Python project:

```bash
(venv) $ export PYTHONPATH="./:$PYTHONPATH"
```

First, run the nodes. Type the following command in `m` terminals to initiate them:

```bash
(venv) $ python node/main.py [0-m]
```
**Note:** To run multiple nodes using a single command, you can use:

```bash
(venv) $ for i in {0..m}; do python node/main.py $i & done

```

After executing the command, wait until the node setup is complete. The setup is finished when the node API is printed along with a message indicating **Waiting for incoming connections...**

Finally, run the gateway in the last terminal:

```bash
(venv) $ python gateway/main.py [number of nodes you ran] [threshold] [n] [number of signatures]
```

The gateway takes 4 parameters as input:
1. `number of nodes you ran`: The number of active nodes.
2. `threshold`: The threshold of the FROST algorithm, which is an integer ($t \leq n$).
3. `n`: The number of nodes cooperating with the gateway to generate a distributed key ($n \leq m$).
4. `number of signatures`: The number of signatures requested by the gateway upon completion of the Distributed Key Generation (DKG).


**Note:** Logs for each node and the gateway are stored in the `./logs` directory.

## Benchmarking

This evaluation is done on the Intel i7-13000H with 8 core and 16GB RAM

|           Benchmark           | DKG | Nonces per Node | Signing |
|:-----------------------------:|:---:|:---------------:|:-------:|
| 15 of 20 With 30 Active Nodes |  5  |         7       |     5   |
| 25 of 30 With 40 Active Nodes |  8  |         8       |     9   |

---
