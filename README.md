About
-----

`zklock.py` allows you to run any shell command while acquiring distributed lock over Zookeeper, similar what [flock](https://linux.die.net/man/1/flock) does except it acquires local lock (over local file).


Requirements
------------

This script requires `kazoo` python module, you can find out more about it [here](https://kazoo.readthedocs.io/en/latest/index.html)


Usage
-----

Command line only
```
zklock.py --server zookeeper.example.com --port 2181 --project test --command "service test restart"
```

Command line with configuration file
`zklock.conf`
```
[zklock]
server = zookeeper.example.com
port = 2181
lock_timeout = 10
project = test
command = service test restart
```

```
zklock.py --config zklock.conf
```

Also if you want or need to, you can simulate different states by using `true`/`false` commands

Simulate `OK` state
```
zklock.py --server zookeeper.example.com --port 2181 --project test --command true
```

Simulate `FAILED` state
```
zklock.py --server zookeeper.example.com --port 2181 --project test --command false
```


License and Authors
-------------------
**Author**: Milos Buncic
