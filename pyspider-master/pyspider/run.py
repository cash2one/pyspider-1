#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-03-05 00:11:49

import os
import sys
import six
import socket
import copy
import time
import json
import shutil
import logging
import logging.config
import ConfigParser

import click
import pyspider
from pyspider.message_queue import connect_message_queue
from pyspider.database import connect_database
from pyspider.libs import utils
from pyspider.libs import read_project_config
from pyspider.database.base.taskdb import TaskDB


def read_config(ctx, param, value):
    if not value:
        return {}
    import json

    def underline_dict(d):
        if not isinstance(d, dict):
            return d
        return dict((k.replace('-', '_'), underline_dict(v)) for k, v in six.iteritems(d))

    config = underline_dict(json.load(value))
    ctx.default_map = config
    return config


def connect_db(ctx, param, value):
    if not value:
        return
    return utils.Get(lambda: connect_database(value))


def load_cls(ctx, param, value):
    if isinstance(value, six.string_types):
        return utils.load_object(value)
    return value


def connect_rpc(value):
    if not value:
        return
    try:
        from six.moves import xmlrpc_client
    except ImportError:
        import xmlrpclib as xmlrpc_client
    return xmlrpc_client.ServerProxy(value, allow_none=True)


@click.group(invoke_without_command=True)
@click.option('-c', '--config', callback=read_config, type=click.File('r'), help='a json file with default values for subcommands.',
              default=os.path.join(os.getcwd(), './conf/sys.ini'))
@click.option('--project-config', help='initialized project config.',
              default=os.path.join(os.getcwd(), './conf/config.ini'))
@click.option('--logging-config', default=os.path.join(os.path.dirname(__file__), "log/logging.conf"),
              help="logging config file for built-in python logging module", show_default=True)
@click.option('--debug', envvar='DEBUG', default=False, is_flag=True, help='debug mode')
@click.option('--queue-maxsize', envvar='QUEUE_MAXSIZE', default=0,
              help='maxsize of queue')
@click.option('--taskdb', envvar='TASKDB', callback=connect_db,
              help='database url for taskdb, default: sqlite')
@click.option('--projectdb', envvar='PROJECTDB', callback=connect_db,
              help='database url for projectdb, default: sqlite')
@click.option('--resultdb', envvar='RESULTDB', callback=connect_db,
              help='database url for resultdb, default: sqlite')
@click.option('--message-queue', envvar='AMQP_URL',
              help='connection url to message queue, '
              'default: builtin multiprocessing.Queue')
@click.option('--amqp-url', help='[deprecated] amqp url for rabbitmq. '
              'please use --message-queue instead.')
@click.option('--beanstalk', envvar='BEANSTALK_HOST',
              help='[deprecated] beanstalk config for beanstalk queue. '
              'please use --message-queue instead.')
@click.option('--phantomjs-proxy', envvar='PHANTOMJS_PROXY', help="phantomjs proxy1 ip:port1,phantomjs proxy2 ip:port2")
@click.option('--data-path', default='./data', help='data dir path')
@click.option('--add-sys-path/--not-add-sys-path', default=True, is_flag=True,
              help='add current working directory to python lib search path')
@click.version_option(version=pyspider.__version__, prog_name=pyspider.__name__)
@click.pass_context
def cli(ctx, **kwargs):
    """
    A powerful spider system in python.
    """
    if kwargs['add_sys_path']:
        sys.path.append(os.getcwd())

    logging.config.fileConfig(kwargs['logging_config'])

    if not kwargs['project_config'] or not os.path.exists(kwargs['project_config']):
        kwargs['project_config'] = os.path.join(os.getcwd(), './conf/config.ini')

    # get db from env
    for db in ('taskdb', 'projectdb', 'resultdb'):
        if kwargs[db] is not None:
            continue
        if os.environ.get('MYSQL_NAME'):
            kwargs[db] = utils.Get(lambda db=db: connect_database(
                'sqlalchemy+mysql+%s://%s:%s/%s' % (
                    db, os.environ['MYSQL_PORT_3306_TCP_ADDR'],
                    os.environ['MYSQL_PORT_3306_TCP_PORT'], db)))
        elif os.environ.get('MONGODB_NAME'):
            kwargs[db] = utils.Get(lambda db=db: connect_database(
                'mongodb+%s://%s:%s/%s' % (
                    db, os.environ['MONGODB_PORT_27017_TCP_ADDR'],
                    os.environ['MONGODB_PORT_27017_TCP_PORT'], db)))
        elif ctx.invoked_subcommand == 'bench':
            if kwargs['data_path'] == './data':
                kwargs['data_path'] += '/bench'
                shutil.rmtree(kwargs['data_path'], ignore_errors=True)
                os.mkdir(kwargs['data_path'])
            if db in ('taskdb', 'resultdb'):
                kwargs[db] = utils.Get(lambda db=db: connect_database('sqlite+%s://' % (db)))
            else:
                kwargs[db] = utils.Get(lambda db=db: connect_database('sqlite+%s:///%s/%s.db' % (
                    db, kwargs['data_path'], db[:-2])))
        else:
            if not os.path.exists(kwargs['data_path']):
                os.mkdir(kwargs['data_path'])
            kwargs[db] = utils.Get(lambda db=db: connect_database('sqlite+%s:///%s/%s.db' % (
                db, kwargs['data_path'], db[:-2])))
            kwargs['is_%s_default' % db] = True

    # create folder for counter.dump
    if not os.path.exists(kwargs['data_path']):
        os.mkdir(kwargs['data_path'])

    # message queue, compatible with old version
    if kwargs.get('message_queue'):
        pass
    elif kwargs.get('amqp_url'):
        kwargs['message_queue'] = kwargs['amqp_url']
    elif os.environ.get('RABBITMQ_NAME'):
        kwargs['message_queue'] = ("amqp://guest:guest@%(RABBITMQ_PORT_5672_TCP_ADDR)s"
                                   ":%(RABBITMQ_PORT_5672_TCP_PORT)s/%%2F" % os.environ)
    elif kwargs.get('beanstalk'):
        kwargs['message_queue'] = "beanstalk://%s/" % kwargs['beanstalk']

    for name in ('newtask_queue', 'status_queue', 'scheduler2fetcher',
                 'fetcher2processor', 'processor2result'):
        if kwargs.get('message_queue'):
            kwargs[name] = utils.Get(lambda name=name: connect_message_queue(
                name, kwargs.get('message_queue'), kwargs['queue_maxsize']))
        else:
            kwargs[name] = connect_message_queue(name, kwargs.get('message_queue'),
                                                 kwargs['queue_maxsize'])

    if kwargs.get('phantomjs_proxy'):
        pass
    elif os.environ.get('PHANTOMJS_NAME'):
        kwargs['phantomjs_proxy'] = os.environ['PHANTOMJS_PORT_25555_TCP'][len('tcp://'):]

    ctx.obj = utils.ObjectDict(ctx.obj or {})
    ctx.obj['instances'] = []
    ctx.obj.update(kwargs)

    cf = ConfigParser.ConfigParser()
    cf.read(ctx.obj.get('project_config'))
    ctx.obj['cf'] = cf

    if ctx.invoked_subcommand is None:
        logging.info('=======invoke stand alone mode========')
        ctx.invoke(stand_alone)
    return ctx


@cli.command()
@click.option('--xmlrpc/--no-xmlrpc', default=True)
@click.option('--xmlrpc-host', default='127.0.0.1')
@click.option('--xmlrpc-port', envvar='SCHEDULER_XMLRPC_PORT', default=23333)
@click.option('--inqueue-limit', default=0,
              help='size limit of task queue for each project, '
              'tasks will been ignored when overflow')
@click.option('--delete-time', default=5 * 60,
              help='delete time before marked as delete')
@click.option('--active-tasks', default=0, help='active log size')
@click.option('--loop-limit', default=1000, help='maximum number of tasks due with in a loop')
@click.option('--scheduler-cls', default='pyspider.scheduler.Scheduler', callback=load_cls,
              help='scheduler class to be used.')
@click.pass_context
def scheduler(ctx, xmlrpc, xmlrpc_host, xmlrpc_port,
              inqueue_limit, delete_time, active_tasks, loop_limit, scheduler_cls):
    """
    Run Scheduler, only one scheduler is allowed.
    """
    g = ctx.obj
    Scheduler = load_cls(None, None, scheduler_cls)

    scheduler = Scheduler(taskdb=g.taskdb, projectdb=g.projectdb, resultdb=g.resultdb,
                          newtask_queue=g.newtask_queue, status_queue=g.status_queue,
                          out_queue=g.scheduler2fetcher, data_path=g.get('data_path', 'data'))
    scheduler.INQUEUE_LIMIT = inqueue_limit
    scheduler.DELETE_TIME = delete_time
    scheduler.ACTIVE_TASKS = active_tasks
    scheduler.LOOP_LIMIT = loop_limit

    g.instances.append(scheduler)
    if g.get('testing_mode'):
        return scheduler

    if xmlrpc:
        utils.run_in_thread(scheduler.xmlrpc_run, port=xmlrpc_port, bind=xmlrpc_host)
    scheduler.run()


@cli.command()
@click.option('--xmlrpc/--no-xmlrpc', default=False)
@click.option('--xmlrpc-host', default='0.0.0.0')
@click.option('--xmlrpc-port', envvar='FETCHER_XMLRPC_PORT', default=24444)
@click.option('--poolsize', default=100, help="max simultaneous fetches")
@click.option('--proxy', help="proxy host:port")
@click.option('--user-agent', help='user agent')
@click.option('--timeout', help='default fetch timeout')
@click.option('--fetcher-cls', default='pyspider.fetcher.Fetcher', callback=load_cls,
              help='Fetcher class to be used.')
@click.pass_context
def fetcher(ctx, xmlrpc, xmlrpc_host, xmlrpc_port, poolsize, proxy, user_agent,
            timeout, fetcher_cls, async=True):
    """
    Run Fetcher.
    """
    g = ctx.obj
    Fetcher = load_cls(None, None, fetcher_cls)

    fetcher = Fetcher(inqueue=g.scheduler2fetcher, outqueue=g.fetcher2processor,
                      poolsize=poolsize, proxy=proxy, async=async)
    fetcher.phantomjs_proxy = g.phantomjs_proxy
    if user_agent:
        fetcher.user_agent = user_agent
    if timeout:
        fetcher.default_options = copy.deepcopy(fetcher.default_options)
        fetcher.default_options['timeout'] = timeout

    g.instances.append(fetcher)
    if g.get('testing_mode'):
        return fetcher

    if xmlrpc:
        utils.run_in_thread(fetcher.xmlrpc_run, port=xmlrpc_port, bind=xmlrpc_host)
    fetcher.run()


@cli.command()
@click.option('--processor-cls', default='pyspider.processor.Processor',
              callback=load_cls, help='Processor class to be used.')
@click.pass_context
def processor(ctx, processor_cls, enable_stdout_capture=False):
    """
    Run Processor.
    """
    g = ctx.obj
    Processor = load_cls(None, None, processor_cls)

    processor = Processor(projectdb=g.projectdb,
                          inqueue=g.fetcher2processor, status_queue=g.status_queue,
                          newtask_queue=g.newtask_queue, result_queue=g.processor2result,
                          enable_stdout_capture=enable_stdout_capture)

    g.instances.append(processor)
    if g.get('testing_mode'):
        return processor

    processor.run()


@cli.command()
@click.option('--result-cls', default='pyspider.result.ResultWorker', callback=load_cls,
              help='ResultWorker class to be used.')
@click.pass_context
def result_worker(ctx, result_cls):
    """
    Run result worker.
    """
    logging.info(result_cls)
    g = ctx.obj
    ResultWorker = load_cls(None, None, result_cls)

    result_worker = ResultWorker(resultdb=g.resultdb, inqueue=g.processor2result)

    g.instances.append(result_worker)
    if g.get('testing_mode'):
        return result_worker

    result_worker.run()


@cli.command()
@click.option('--phantomjs-path', default='phantomjs', help='phantomjs path')
@click.option('--port', default=25555, help='phantomjs port')
@click.option('--auto-restart', default=False, help='auto restart phantomjs if crashed')
@click.argument('args', nargs=-1)
@click.pass_context
def phantomjs(ctx, phantomjs_path, port, auto_restart, args):
    """
    Run phantomjs fetcher if phantomjs is installed.
    """
    args = args or ctx.default_map and ctx.default_map.get('args', [])

    import subprocess
    g = ctx.obj
    _quit = []
    phantomjs_fetcher = os.path.join(
        os.path.dirname(pyspider.__file__), 'fetcher/phantomjs_fetcher.js')
    cmd = [phantomjs_path,
           # this may cause memory leak: https://github.com/ariya/phantomjs/issues/12903
           #'--load-images=false',
           '--ssl-protocol=any',
           '--disk-cache=true',
           '--output-encoding=utf-8'] + list(args or []) + [phantomjs_fetcher, str(port)]

    try:
        _phantomjs = subprocess.Popen(cmd)
    except OSError:
        logging.warning('phantomjs not found, continue running without it.')
        return None

    def quit(*args, **kwargs):
        _quit.append(1)
        _phantomjs.kill()
        _phantomjs.wait()
        logging.info('phantomjs existed.')

    if not g.get('phantomjs_proxy'):
        g['phantomjs_proxy'] = '127.0.0.1:%s' % port

    phantomjs = utils.ObjectDict(port=port, quit=quit)
    g.instances.append(phantomjs)
    if g.get('testing_mode'):
        return phantomjs

    while True:
        _phantomjs.wait()
        if _quit or not auto_restart:
            break
        _phantomjs = subprocess.Popen(cmd)


@cli.command()
@click.option('--fetcher-num', default=1, help='instance num of fetcher')
@click.option('--processor-num', default=1, help='instance num of processor')
@click.option('--result-worker-num', default=1,
              help='instance num of result worker')

@click.option('--run-in', default='thread', type=click.Choice(['subprocess', 'thread']),
              help='run each components in thread or subprocess. '
              'always using thread for windows.')
@click.option('--delete-mod', help='delete project when system invoke.', default='2')
@click.option('--not-delete', help='project not delete when system invoke', default='')
@click.pass_context
def stand_alone(ctx, fetcher_num, processor_num, result_worker_num, run_in, delete_mod, not_delete):
    """
    stand alone mode, run in command line
    """
    g = ctx.obj

    try:
        os.remove(os.path.join(g['data_path'], 'scheduler.1h'))
        os.remove(os.path.join(g['data_path'], 'scheduler.1d'))
        os.remove(os.path.join(g['data_path'], 'scheduler.all'))
    except Exception as e:
        pass

    def clear_all_project(black_list=None):
        if black_list is None:
            black_list = []
        for project in list(ctx.obj.projectdb.get_all()):
            project_name = project['name'].encode('utf-8')
            if project_name not in black_list:
                logging.info('==========delete old project: %s==========' % project_name)
                project_name = project_name.decode('utf-8')
                ctx.obj.taskdb.drop(project_name)
                ctx.obj.projectdb.drop(project_name)
                ctx.obj.resultdb.drop(project_name)

    delete_mod = int(delete_mod)
    projects = not_delete.split(',')
    # delete all
    if delete_mod == 2:
        clear_all_project()
    # only delete old
    elif delete_mod == 1:
        clear_all_project(projects)

    if run_in == 'subprocess' and os.name != 'nt':
        run_in = utils.run_in_subprocess
    else:
        run_in = utils.run_in_thread

    # build instance
    threads = []

    try:
        # phantomjs
        if not g.get('phantomjs_proxy'):
            phantomjs_config = g.config.get('phantomjs', {})
            phantomjs_config.setdefault('auto_restart', True)
            threads.append(run_in(ctx.invoke, phantomjs, **phantomjs_config))
            time.sleep(2)
            if threads[-1].is_alive() and not g.get('phantomjs_proxy'):
                g['phantomjs_proxy'] = '127.0.0.1:%s' % phantomjs_config.get('port', 25555)

        # result worker
        result_worker_config = g.config.get('result_worker', {})
        for i in range(result_worker_num):
            threads.append(run_in(ctx.invoke, result_worker, **result_worker_config))

        # processor
        processor_config = g.config.get('processor', {})
        for i in range(processor_num):
            threads.append(run_in(ctx.invoke, processor, **processor_config))

        # fetcher
        fetcher_config = g.config.get('fetcher', {})
        fetcher_config.setdefault('xmlrpc_host', '127.0.0.1')
        for i in range(fetcher_num):
            threads.append(run_in(ctx.invoke, fetcher, **fetcher_config))

        # scheduler
        scheduler_config = g.config.get('scheduler', {})
        scheduler_config.setdefault('xmlrpc_host', '127.0.0.1')
        threads.append(run_in(ctx.invoke, scheduler, **scheduler_config))

        while True:
            time.sleep(10)
            logging.info('=============================crwaling==========================')
    finally:
        # exit components run in threading
        for each in g.instances:
            each.quit()

        # exit components run in subprocess
        for each in threads:
            if not each.is_alive():
                continue
            if hasattr(each, 'terminate'):
                each.terminate()
            each.join()


def get_config(config, scheduler_rpc=None):
    """
    get scheduler rpc address, if not exist, use default address.
    default address is http://127.0.0.1:23333
    """
    config['queues'] = dict()
    for name in ('newtask_queue', 'status_queue', 'scheduler2fetcher',
                 'fetcher2processor', 'processor2result'):
        config['queues'][name] = getattr(config, name, None)

    if isinstance(scheduler_rpc, six.string_types):
        scheduler_rpc = connect_rpc(scheduler_rpc)
    if scheduler_rpc is None and os.environ.get('SCHEDULER_NAME'):
        config['scheduler_rpc'] = connect_rpc('http://%s/' % (
            os.environ['SCHEDULER_PORT_23333_TCP'][len('tcp://'):]))
    elif scheduler_rpc is None:
        config['scheduler_rpc'] = connect_rpc('http://127.0.0.1:23333/')
    else:
        config['scheduler_rpc'] = scheduler_rpc
    return config


def project_update(config, project_name, key, value):
    """
    update project key by given value, key should be in ['group', 'status', 'rate']
    """
    projectdb = config.projectdb

    project_info = projectdb.get(project_name, fields=('name', 'group'))
    if not project_info:
        logging.warning("update project: no such project.")

    if key not in ('group', 'status', 'rate'):
        logging.info('unknown field: %s' % key)
        return False
    if key == 'rate':
        value = value.split('/')
        if len(value) != 2:
            logging.warning('format error: rate/burst')
            return False
        rate = float(value[0])
        burst = float(value[1])
        update = {
            'rate': min(rate, config.get('max_rate', rate)),
            'burst': min(burst, config.get('max_burst', burst)),
        }
    else:
        update = {
            key: value
        }

    ret = projectdb.update(project_name, update)
    if ret:
        rpc = config['scheduler_rpc']
        if rpc is not None:
            try:
                rpc.update_project()
            except socket.error as e:
                logging.warning('connect to scheduler rpc error: %r', e)
                return False
    time.sleep(1)
    return True


@cli.command()
@click.argument('project', nargs=1)
@click.pass_context
def update(ctx, project):
    """
    update project while running, run in command line
    """
    g = ctx.obj
    g = get_config(g)
    projectdb = g.projectdb
    project_info = projectdb.get(project, fields=['name', 'status', 'group'])
    if not project_info:
        logging.error('project %s not exist!' % project)
        return
    if project_info.get('status') == 'DELETE':
        logging.warning("project %s is deleted." % project)
        return
    g = get_config(g)
    cf = g.get('cf')
    from pyspider.spider.gen_base_spider import one_local_project
    try:
        project_name, project = one_local_project(cf, project)
    except TypeError:
        logging.error('config file has no such section: %s.' % project)
        return
    except Exception as e:
        err = str(e)
        logging.error(err)
        return
    if not project['script']:
        logging.error('find no crawler script for project %s!' % project_name)
        return
    project_info['script'] = project['script']
    try:
        ret = read_project_config.read_project_config(cf, project_name)
    except Exception as e:
        logging.error(str(e))
        return
    project_info.update(ret)
    if not read_project_config.check_project(project_info):
        logging.warning("check project %s Fail!" % project_name)
        return
    if project_info.get('status') in ('DEBUG', 'RUNNING', ):
        project_info['status'] = 'STOP'
    projectdb.update(project_name, project_info)
    rpc = g['scheduler_rpc']
    if rpc is not None:
        try:
            rpc.update_project()
        except socket.error as e:
            logging.warning('connect to scheduler rpc error: %r', e)
            return
    time.sleep(1)
    project_update(g, project_name, 'status', 'RUNNING')
    logging.info('update project %s success.' % project_name)


@cli.command()
@click.pass_context
@click.argument('project', nargs=1)
@click.option('--delete-time', default='-1',
              help='project delete delay time.')
def delete(ctx, project, delete_time):
    """
    delete exsiting project by paramter 'project', delete all projects if 'project' equals 'all
    the project will be actually deleted after few minutes.
    '"""
    g = ctx.obj
    projectdb = g.projectdb
    g = get_config(g)

    delete_time = int(delete_time)
    if delete_time < 0:
        delete_time = -1

    def delete_one(_project, _project_info):
        if not _project_info:
            logging.warning('project %s not exist!', _project)
            return
        if _project_info.get('status') == 'DELETE':
            logging.warning('project %s is already deleted before!', _project)
            return
        else:
            _project_info['status'] = 'DELETE'
            _project_info['group'] = 'delete'
            _project_info['deletetime'] = delete_time
            projectdb.update(_project, _project_info)
            logging.info('delete project: %s' % _project)

    if project == 'ALL':
        for project_info in list(g.projectdb.get_all(fields=['name', 'status', 'group'])):
            delete_one(project_info.get('name'), project_info)
    else:
        project_info = projectdb.get(project, fields=['name', 'status', 'group', 'deletetime'])
        delete_one(project, project_info)

    rpc = g['scheduler_rpc']
    if rpc is not None:
        try:
            rpc.update_project()
        except socket.error as e:
            logging.warning('connect to scheduler rpc error: %r', e)
            return


@cli.command()
@click.pass_context
@click.argument('project', nargs=1)
def run(ctx, project):
    """
    run project, the status of project could be 'DEBUG', 'RUNNING', 'STOP'
    """
    g = ctx.obj
    g = get_config(g)
    projectdb = g.projectdb
    project_info = projectdb.get(project, fields=['name', 'status', 'group'])
    if not project_info:
        logging.error('project %s is not exist!' % project)
        return
    # if task in RUNNING or DEBUG status, do not update its status
    if project_info.get('status') == 'DELETE':
        logging.error('project %s is deleted!' % project)
        return
    if project_info.get('status') not in ('DEBUG', 'RUNNING', ):
        project_update(g, project, 'status', 'RUNNING')
        time.sleep(1)
    newtask = {
        "project": project,
        "taskid": "on_start",
        "url": "data:,on_start",
        "process": {
            "callback": "on_start",
        },
        "schedule": {
            "priority": 8,
            "force_update": True,
        },
        'depth': -1,
    }
    rpc = g['scheduler_rpc']
    try:
        rpc.newtask(newtask)
    except socket.error as e:
        logging.error('connect to scheduler rpc error: %r', e)
    logging.info('run project %s success!' % project)


@cli.command()
@click.pass_context
@click.argument('project', nargs=1)
def add_project(ctx, project=None):
    """
    add project by given config
    """
    g = ctx.obj
    projectdb = g.projectdb
    project_info = projectdb.get(project, fields=['name', 'status', 'group'])
    if project_info:
        if project_info['status'] == 'DELETE':
            logging.error('project %s is still deleted, wait util delete operator done.' % project)
        else:
            logging.error('project %s is already exist.' % project)
        return
    g = get_config(g)
    cf = g.get('cf')
    from pyspider.spider.gen_base_spider import one_local_project
    try:
        project_name, project = one_local_project(cf, project)
    except TypeError:
        logging.error('config file has no such section: %s.' % project)
        return
    except Exception as e:
        err = str(e)
        logging.error(err)
        return
    if not project['script']:
        logging.error('find no crawler script for project %s!' % project_name)
        return
    if not projectdb.verify_project_name(project_name):
        logging.info('project name is not allowed!')
        return
    project_info = {
        'name': project_name,
        'script': project['script'],
        'status': 'TODO',
    }
    try:
        ret = read_project_config.read_project_config(cf, project_name)
    except Exception as e:
        logging.error(str(e))
        return

    project_info.update(ret)
    if not read_project_config.check_project(project_info):
        logging.error('create project %s fail!' % project_name)
        return
    projectdb.insert(project_name, project_info)
    rpc = g['scheduler_rpc']
    if rpc is not None:
        try:
            rpc.update_project()
        except socket.error as e:
            logging.warning('connect to scheduler rpc error: %r', e)
            return
    time.sleep(1)
    ret = project_update(g, project_name, 'status', 'RUNNING')
    if not ret:
        logging.error('create project %s fail!' % project_name)
        return 
    logging.info('create project %s success!' % project_name)


@cli.command()
@click.pass_context
@click.argument('project', default='ALL', nargs=1)
def stop(ctx, project):
    """
    delete exsiting project by paramter 'project', delete all projects if 'project' equals 'all
    '"""
    """TODO, status fix to be DELETE"""
    g = ctx.obj
    projectdb = g.projectdb
    g = get_config(g)

    def stop_one(_project):
        project_info = projectdb.get(_project, fields=['name', 'status', 'group'])
        if not project_info:
            logging.error('no such project: %s' % _project)
        else:
            project_info['status'] = 'STOP'
            projectdb.update(_project, project_info)
            logging.info('stop project: %s' % _project)

    if project == 'ALL':
        for project_name in list(g.projectdb.get_all()):
            stop_one(project_name)
    else:
        stop_one(project)
    rpc = g['scheduler_rpc']
    if rpc is not None:
        try:
            rpc.update_project()
        except socket.error as e:
            logging.warning('connect to scheduler rpc error: %r', e)
            return


def counter(config):
    """
    counter of all projects
    """
    rpc = config['scheduler_rpc']
    if rpc is None:
        return None
    result = {}

    try:
        for project, counter in rpc.counter('5m_time', 'avg').items():
            result.setdefault(project, {})['5m_time'] = counter
        for project, counter in rpc.counter('5m', 'sum').items():
            result.setdefault(project, {})['5m'] = counter
        for project, counter in rpc.counter('1h', 'sum').items():
            result.setdefault(project, {})['1h'] = counter
        for project, counter in rpc.counter('1d', 'sum').items():
            result.setdefault(project, {})['1d'] = counter
        for project, counter in rpc.counter('all', 'sum').items():
            result.setdefault(project, {})['all'] = counter
    except socket.error as e:
        logging.warning('connect to scheduler rpc error: %r', e)
        return None

    return result


@cli.command()
@click.pass_context
@click.argument('project', default='ALL', nargs=1)
def get_info(ctx, project):
    """
    get info of project, include status, rate/burst, crawler counter
    TODO: format the output
    """
    g = ctx.obj
    projectdb = g.projectdb
    g = get_config(g)
    counters = counter(g)
    if project == 'ALL':
        project_infos = projectdb.get_all(fields=['name', 'status', 'group', 'rate', 'burst', 'updatetime'])
        for project_info in project_infos:
            name = project_info['name']
            if name in counters:
                logging.info("project: %s, group: %s, status: %s, rate/burst: %s/%s, counter: 5m:%s 1h:%s 1d:%s all:%s."
                         % (name, project_info['group'], project_info['status'],
                         project_info['rate'], project_info['burst'],
                         counters[name].get('5m', {'success': 0}).get('success', 0),
                         counters[name].get('1h', {'success': 0}).get('success', 0),
                         counters[name].get('1d', {'success': 0}).get('success', 0),
                         counters[name].get('all', {'success': 0}).get('success', 0)))
    else:
        project_info = projectdb.get(project, fields=['name', 'status', 'group', 'rate', 'burst',
                                                      'updatetime'])
        if not project_info:
            logging.error('project %s not exist.' % project)
            return
        name = project_info['name']
        if name in counters:
            logging.info("project: %s, group: %s, status: %s, rate/burst: %s/%s, counter: 5m:%s 1h:%s 1d:%s all:%s."
                     % (name, project_info['group'], project_info['status'],
                         project_info['rate'], project_info['burst'],
                         counters[name].get('5m', {'success': 0}).get('success', 0),
                         counters[name].get('1h', {'success': 0}).get('success', 0),
                         counters[name].get('1d', {'success': 0}).get('success', 0),
                         counters[name].get('all', {'success': 0}).get('success', 0)))
        else:
            logging.info("project: %s is not running or deleted." % name)
    return


@cli.command()
@click.pass_context
@click.argument('project', nargs=1)
@click.argument('status', default='ALL', nargs=1, type=click.Choice(['ALL', 'SUCCESS', 'ACTIVE', 'FAILED', 'BAD']))
def task_counter(ctx, project, status):
    """restart all tasks of given project"""
    if status == 'ALL':
        status = 0
    else:
        status = TaskDB.status_to_int(status)
    g = ctx.obj
    projectdb = g.projectdb
    taskdb = g.taskdb
    project_info = projectdb.get(project, fields=['name', 'status'])
    if not project_info:
        logging.error('project %s not exist.' % project)
        return
    if project_info['status'] == 'DELETE':
        logging.error('project %s is deleted!' % project)
        return
    try:
        if status == 0:
            tasks_iter = taskdb.get_all_tasks(project=project)
        else:
            tasks_iter = taskdb.load_tasks(status=status, project=project)
    except Exception as e:
        logging.error("load task error: %s" % str(e))
        return
    logging.info("tasks counter is %s" % len(list(tasks_iter)))


@cli.command()
@click.pass_context
@click.argument('project', nargs=1)
@click.argument('status', default='ALL', nargs=1, type=click.Choice(['ALL', 'ACTIVE', 'SUCCESS', 'FAILED', 'BAD']))
def get_seed(ctx, project, status):
    """restart tasks of given project"""
    if status == 'ALL':
        status = 0
    else:
        status = TaskDB.status_to_int(status)
    g = ctx.obj
    projectdb = g.projectdb
    taskdb = g.taskdb
    project_info = projectdb.get(project, fields=['name', 'status'])
    if not project_info:
        logging.error('project %s not exist.' % project)
        return
    try:
        if status == 0:
            tasks_iter = taskdb.get_all_tasks(project=project)
        else:
            tasks_iter = taskdb.load_tasks(status=status, project=project)
    except Exception as e:
        logging.error("load task error: %s" % str(e))
        return
    for task in tasks_iter:
        url = task['url']
        if url.startswith('data:') or url.startswith('curl:'):
            continue
        print url.encode('utf-8')
    return


@cli.command()
@click.pass_context
@click.argument('project', nargs=1)
@click.option('--call-back', default='_no_follow', help='html crawler callback.')
@click.option('--seed-path', prompt='please input seed path', help='seed path to be used.')
def add_seed(ctx, project, call_back, seed_path):
    if not os.path.exists(seed_path):
        logging.error('%s not exist!' % seed_path)
        return
    g = ctx.obj
    projectdb = g.projectdb
    project_info = projectdb.get(project, fields=['name', 'status', 'follow'])
    if not project_info:
        logging.error('project %s not exist.' % project)
        return
    if project_info['status'] == "DELETE":
        logging.error('projet %s is deleted!' % project)
        return
    if project_info['follow'] != -1:
        logging.error('only html crawler could add seed!')
        return
    g = get_config(g)
    rpc = g['scheduler_rpc']
    if rpc is not None:
        try:
            rpc.add_seed(seed_path, project, call_back)
        except socket.error as e:
            logging.warning('connect to scheduler rpc error: %r', e)
            return False
    logging.info('add seed urls for project %s success!' % project)
    return


@cli.command()
@click.pass_context
@click.argument('project', nargs=1)
@click.argument('status', nargs=1, type=click.Choice(['SUCCESS', 'FAILED']))
def restart(ctx, project, status):
    """restart all tasks of given project"""
    g = ctx.obj
    projectdb = g.projectdb
    status = TaskDB.status_to_int(status)
    project_info = projectdb.get(project, fields=['name', 'status'])
    if not project_info:
        logging.error('project %s not exist.' % project)
        return
    if project_info['status'] not in ('DEBUG', 'RUNNING', ):
        logging.error('projet %s is not running!' % project)
        return
    g = get_config(g)
    rpc = g['scheduler_rpc']
    if rpc is not None:
        try:
            rpc.restart(project, status)
        except socket.error as e:
            logging.warning('connect to scheduler rpc error: %r', e)
            return False

    if status == 2:
        logging.info("restart success tasks of project %s success" % project)
    else:
        logging.info("restart fail tasks of project %s success" % project)
    return

@cli.command()
@click.pass_context
@click.argument('host', nargs=1)
@click.argument('rate', nargs=1)
@click.argument('burst', nargs=1)
def set_host_bucket(ctx, host, rate, burst):
    """set limit of given host"""
    g = ctx.obj
    g = get_config(g)
    rpc = g['scheduler_rpc']
    if rpc is not None:
        try:
            rpc.set_host_bucket(host, float(rate), float(burst))
        except socket.error as e:
            logging.warning('connect to scheduler rpc error: %r', e)
            return False
    logging.info('set host bucket success!')
    return


@cli.command()
@click.pass_context
@click.argument('project', nargs=1)
def get_all_result(ctx, project):
    g = ctx.obj
    resultdb = g.resultdb
    resultdb.get(project, 'any')
    if project not in resultdb.projects:
        logging.error("no such project.")
        return
    results = resultdb.select(project, offset=0, limit=0)
    for result in results:
        print json.dumps(result, ensure_ascii=False).encode('utf-8')



@cli.command()
@click.pass_context
@click.argument('project', nargs=1)
@click.argument('begin_time', nargs=1, default='0')
@click.argument('end_time', nargs=1, default='0')
def get_result(ctx, project, begin_time, end_time):
    g = ctx.obj
    if begin_time != '0':
        begin_time = int(time.mktime(time.strptime(begin_time, '%Y-%m-%d %H:%M:%S')))
    else:
        begin_time = 0
    if end_time != '0':
        end_time = int(time.mktime(time.strptime(end_time, '%Y-%m-%d %H:%M:%S')))
    else:
        end_time = 0
    resultdb = g.resultdb
    resultdb.get(project, 'any')
    if project not in resultdb.projects:
        logging.error("no such project.")
        return
    results = resultdb.select(project, offset=0, limit=0)
    for result in results:
        result_time = int(result['updatetime'])
        if begin_time != 0 and result_time < begin_time:
            continue
        if end_time != 0 and result_time > end_time:
            continue
        print json.dumps(result, ensure_ascii=False).encode('utf-8')


def main():
    cli()

if __name__ == '__main__':
    main()
