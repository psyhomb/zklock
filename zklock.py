#!/usr/bin/env python2
# Author: Milos Buncic
# Date: 2016/05/11
# Description: Acquire zookeeper lock
#
#
# Configuration file example (zklock.conf):
#
# [zklock]
# server = zookeeper.example.com
# port = 2181
# lock_timeout = 10
# delay_exec = 1
# project = test
# command = service test restart

from kazoo.client import KazooClient, KazooState
import kazoo.exceptions
import argparse
import subprocess
import shlex
import time
import os, sys
import json
from socket import getfqdn
from ConfigParser import SafeConfigParser


# Default values
zk_server = '127.0.0.1'
zk_port = 2181
zk_lock_timeout = 10
zk_delay_exec = 1


def argsParser():
  """ Return args collected from cmd line (output: dict) """
  parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('-C', '--config', help='Path to the configuration file', dest='config', action='store')
  parser.add_argument('-s', '--server', help='Zookeeper server FQDN or IP', default=zk_server, dest='server', action='store')
  parser.add_argument('-p', '--port', help='Zookeeper server port', default=zk_port, type=int, dest='port', action='store')
  parser.add_argument('-t', '--lock-timeout', help='How long to wait to acquire lock', default=zk_lock_timeout, type=int, dest='lock_timeout', action='store')
  parser.add_argument('-d', '--delay-exec', help='Delay command execution', default=zk_delay_exec, type=int, dest='delay_exec', action='store')
  parser.add_argument('-P', '--project', help='Project name', dest='project', action='store')
  parser.add_argument('-c', '--command', help='Command to run', dest='command', action='store')

  d = parser.parse_args().__dict__
  if d['config'] is not None and os.path.isfile(d['config']):
    config_parser = SafeConfigParser()
    config_parser.read(d['config'])

    for k,v in config_parser.items('zklock'):
      d[k] = v

  if d['command'] is None or d['project'] is None:
    parser.print_help()
    parser.exit(1)

  return d


def cmd(command_line):
  """ Return output of a system command (output: dict) """
  process = subprocess.Popen(shlex.split(command_line), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  output, error = process.communicate()

  return {'output': output, 'error': error, 'code': process.returncode}


args = argsParser()
# Script name w/o extension
script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
zk_server = args['server']
zk_port = int(args['port'])
zk_lock_path = '/%s-%s/lock' % (script_name, args['project'])
zk_status_path = '/%s-%s/status' % (script_name, args['project'])
zk_lock_timeout = int(args['lock_timeout'])
zk_delay_exec = int(args['delay_exec'])
command = args['command']
fqdn = getfqdn()

zk = KazooClient('%s:%d' % (zk_server, zk_port))
zk.start()

lock = zk.Lock(zk_lock_path, fqdn)

print 'Current lock contenders are: %s' % ', '.join(lock.contenders())

try:
  lock.acquire(blocking=True, timeout=zk_lock_timeout)
  print 'Lock successfully acquired\n'
except kazoo.exceptions.LockTimeout as lt:
  print 'LockTimeout: %s' % lt
  sys.exit(1)

d = {}
if zk.exists(zk_status_path) is None:
  d[fqdn] = 'UNKNOWN'
  zk.create(zk_status_path, '%s' % json.dumps(d), makepath=True)

d = json.loads(zk.get(zk_status_path)[0])
for node, status in d.items():
  if node != fqdn:
    if status == 'FAILED' or status == 'INPROGRESS':
      print 'Previous node (%s) has failed or has been interrupted, exiting...' % node
      lock.release()
      sys.exit(1)

d[fqdn] = 'INPROGRESS'
zk.set(zk_status_path, '%s' % json.dumps(d))


#########################
time.sleep(zk_delay_exec)
output = cmd(command)
print output['output']
#########################


if output['code'] == 0:
  d[fqdn] = 'OK'
else:
  d[fqdn] = 'FAILED'

zk.set(zk_status_path, '%s' % json.dumps(d))

lock.release()
print 'Lock successfully released'
