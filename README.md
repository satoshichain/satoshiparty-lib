[![Build Status Travis](https://travis-ci.org/ShellpartySHP/shellparty-lib.svg?branch=develop)](https://travis-ci.org/ShellpartySHP/shellparty-lib)
[![Build Status Circle](https://circleci.com/gh/ShellpartySHP/shellparty-lib.svg?&style=shield)](https://circleci.com/gh/ShellpartySHP/shellparty-lib)
[![Coverage Status](https://coveralls.io/repos/ShellpartySHP/shellparty-lib/badge.png?branch=develop)](https://coveralls.io/r/ShellpartySHP/shellparty-lib?branch=develop)
[![Latest Version](https://pypip.in/version/shellparty-lib/badge.svg)](https://pypi.python.org/pypi/shellparty-lib/)
[![License](https://pypip.in/license/shellparty-lib/badge.svg)](https://pypi.python.org/pypi/shellparty-lib/)
[![Gitter chat](https://badges.gitter.im/gitterHQ/gitter.png)](https://gitter.im/ShellpartySHP/General)


# Description
`shellparty-lib` is the reference implementation of the [Shellparty Protocol](https://shellparty.io).

**Note:** for the command-line interface that used to be called `shellpartyd`, see [`shellparty-cli`](https://github.com/ShellpartySHP/shellparty-cli).


# Requirements
* [Patched Shellcoin Core](https://github.com/shelldrak/SatoshiChain/releases) with the following options set:

	```
	rpcuser=SatoshiChainrpc
	rpcpassword=<password>
	server=1
	txindex=1
	addrindex=1
	rpcthreads=1000
	rpctimeout=300
	minrelaytxfee=0.00005
	limitfreerelay=0
	```


# Installation

```
$ git clone https://github.com/ShellpartySHP/shellparty-lib.git
$ cd shellparty-lib
$ python3 setup.py install
```


# Usage

```
$ python3
>>> from shellpartylib import server
>>> db = server.initialise(<options>)
>>> server.start_all(db)
```


# Further Reading

* [Official Project Documentation](http://shellparty.io/docs/)
