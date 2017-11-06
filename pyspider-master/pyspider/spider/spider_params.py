# -*- coding:utf-8 -*
# 爬虫中可用的配置参数
params = ['url', 'callback', 'method', 'params', 'data', 'files', 'headers',
          'timeout', 'allow_redirects', 'cookies', 'proxy', 'etag', 'last_modifed',
          'auto_recrawl', 'fetch_type', 'js_run_at', 'js_script',
          'js_viewport_width', 'js_viewport_height', 'depth',
          'load_images', 'priority', 'retries', 'exetime', 'age', 'itag', 'save', 'taskid']

next_params = ['headers', 'allow_redirects', 'cookies']

def rebuild_all_params(config):
    _config = {}
    for each in params:
        if each in config and config[each]:
            _config[each] = config[each]
    return _config

def rebuild_next_params(config):
    _config = {}
    for each in next_params:
        if each in config and config[each]:
            _config[each] = config[each]
    return _config