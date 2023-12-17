# PyFrost-MPC

This is the MPC (multi-party computation) version of the PyFrost library [(this repositrory)](https://github.com/SAYaghoubnejad/pyfrost) using py-libp2p as the base of party communication.


## How to Setup

To create a virtual environment (`venv`) and install the required packages, run the following commands:

```bash
$ git clone https://github.com/SAYaghoubnejad/pyfrost-mpc.git --recurse-submodules
$ cd pyfrost-mpc
$ virtualenv -p python3.10 venv
$ source venv/bin/activate
(venv) $ pip install .
```

**Note:** The required Python version is `3.10`.

## How to Run

To run the project, first, open `m` additional terminals for `m` nodes and activate the `venv` in these terminals. Note that `m` is an arbitrary positive number, but it must be less than or equal to 99 due to the predefined nodes for testing. Then change the directory to the `tests` folder:

```bash
(venv) $ cd tests
```

First, run the nodes. Type the following command in `m` terminals to initiate them:

```bash
(venv) $ python node/main.py [0-m]
```

**Note:** To run multiple nodes and stop them using a single command, you can run the `run_nodes.sh` and `stop_nodes.sh` scripts. First, add execute permission to them by running the following commands:

```bash
(venv) $ chmod +x run_nodes.sh
(venv) $ chmod +x stop_nodes.sh
```

Run multiple nodes using this command:

```bash
(venv) $ ./run_nodes.sh [number of nodes]
```

After executing either of the above commands, wait until the node setup is complete. The setup is finished when the node API is printed along with a message indicating **Waiting for incoming connections...**

Finally, run `test.py` script in the last terminal:

```bash
(venv) $ python test.py [number of nodes you ran] [threshold] [n] [number of signatures]
```

Note that `test.py` implements the functionality for distributed key generation and signature aggregation.

The script takes 4 parameters as input:

1. `number of nodes you ran`: The number of active nodes.
2. `threshold`: The threshold of the FROST algorithm, which is an integer ($t \leq n$).
3. `n`: The number of nodes cooperating with the DKG to generate a distributed key ($n \leq m$).
4. `number of signatures`: The number of signatures requested by the signature aggregator upon completion of the Distributed Key Generation (DKG).

If you want to stop all the nodes, type the following command:

```bash
(venv) $ ./stop_nodes.sh
```

**Note:** Logs for each node and the signature aggregator are stored in the `./logs` directory.

## Benchmarking

This evaluation is done on the Intel i7-6700HQ with 8 cores and 16GB RAM. (All times are in seconds)

| Benchmark                     | DKG Time | Nonce Generation Avg. Time per Node | Signing Time |
|-------------------------------|----------|-------------------------------------|--------------|
|  7 of 10                      | 0.840 sec| 0.352 sec                           | 0.135 sec    | 
| 15 of 20                      | 5.435 sec| 0.344 sec                           | 0.380 sec    |
| 25 of 30                      |14.183 sec| 0.345 sec                           | 0.601 sec    |

---

For the non-local evaluation, we incorporated 30 node containers across three distinct countries and four different cities. Additionally, we employed a Signature Aggregator featuring dual vCPUs and an eight-gigabyte RAM configuration.

| Benchmark                     | DKG Time | Nonce Generation Avg. Time per Node | Signing Time |
|-------------------------------|----------|-------------------------------------|--------------|
| 25 of 30                      | 7.400 sec| 1.594 sec                           | 0.725 sec    |

---