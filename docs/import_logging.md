# Logging imports #

If you are finding that a certain module is always being imported and wish to investigate
how the module is being imported, there is now an environment variable that can be set
to print the stack to stderr whenever an import is triggered.

Set `DUCKTOOLS_REPORT_IMPORTS=true` in your environment and you will see `Import triggered:`
followed by the stack trace whenever a lazy importer first imports a module.

Example Output:

```
Import triggered:
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/ducksual/src/ducktools-env/src/ducktools/env/__main__.py", line 525, in <module>
    sys.exit(main())
  File "/home/ducksual/src/ducktools-env/src/ducktools/env/__main__.py", line 515, in main
    result = main_command()
  File "/home/ducksual/src/ducktools-env/src/ducktools/env/__main__.py", line 504, in main_command
    return list_command(manager, args)
  File "/home/ducksual/src/ducktools-env/src/ducktools/env/__main__.py", line 381, in list_command
    if (envs := manager.temp_catalogue.environments) and show_temp:
  File "/home/ducksual/src/ducktools-env/src/ducktools/env/manager.py", line 121, in temp_catalogue
    self._temp_catalogue.expire_caches(self.config.cache_lifetime_delta)
  File "/home/ducksual/src/ducktools-env/src/ducktools/env/catalogue.py", line 431, in expire_caches
    for cachename, cache in self.environments.copy().items():
  File "/home/ducksual/src/ducktools-env/src/ducktools/env/catalogue.py", line 183, in environments
    with self.connection as con:
  File "/home/ducksual/src/ducktools-env/src/ducktools/env/_sqlclasses.py", line 82, in __enter__
    self.connection = _laz.sql.connect(self.db)

```