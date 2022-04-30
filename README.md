# Suzuki-Kasami-Mutual-Exclusion-Algo
---
Project done as part of Distribute system course @ IIIT-H

## Goal
* Implement Suzuki-Kasami’s token-based mutual exclusion protocol for Distributed Systems using MPI4PY. 
* Record and display the status of different nodes on CLI (user has the option to print the (LN or RN) array and queue state values when he queries it).


## How to Run
```
mpiexec -np `X` python3 suzuki-kasami.py `dirc`
```

For `X` number of process and `dirc` directory for logging files.

## Implementation Video

This [link](https://drive.google.com/file/d/1DpjyslyxbWnUoVWtBxOkgTNOAik0VoUV/view?usp=sharing) contains a video depicting the functioning of our algorithm.