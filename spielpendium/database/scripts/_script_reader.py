import glob
import os
import pathlib

from spielpendium import log

__all__ = ['SQLScripts']


class _SQLScriptReader:

    def __init__(self, directory):
        file_list = glob.glob(f'{directory}{os.sep}*.sql')
        self._script_dict = {}

        for script_file in file_list:
            # Open and read the file
            log.logger.debug(f'Reading SQL file: '
                             f'{os.path.basename(script_file)}')
            with open(script_file, 'r') as file:
                sql = file.read()

            log.logger.debug('Successfully read SQL file.')

            # Separate all SQL commands (split on ';')
            sql_commands = tuple([x for x in sql.split(';')
                                  if x.strip() != ''])

            script_name = os.path.splitext(os.path.basename(script_file))[0]
            self._script_dict[script_name] = sql_commands

    def __str__(self):
        keys = [f"'{x}'" for x in self.keys()]
        return f'SQLScripts([{", ".join(keys)}])'

    def __getattr__(self, item):
        if item in self._script_dict.keys():
            return self._script_dict[item]
        elif item in ['all', 'all_scripts']:
            return self._script_dict
        else:
            raise AttributeError(f'{item} is a nonexistent script.')

    def __getitem__(self, item):
        return self._script_dict[item]

    def keys(self):
        return _SQLScriptKeys(self._script_dict.keys())

    def commands(self):
        return list(self._script_dict.values())

    def items(self):
        return zip(self.keys(), self.commands())

    def to_dict(self):
        return {k: v for k, v in self.items()}

    def to_list(self):
        return [(k, v) for k, v in self.items()]

    def __len__(self):
        return len(self._script_dict)


class _SQLScriptKeys:

    def __init__(self, keys):
        self.keys = list(keys)

    def __str__(self):
        keys = [f"'{x}'" for x in self.keys]
        return f'SQLScriptKeys([{", ".join(keys)}])'

    def __getitem__(self, item):
        return self.keys[item]


SQLScripts = _SQLScriptReader(pathlib.Path(__file__).parent.absolute())

if __name__ == '__main__':
    print(SQLScripts.create_database)
    print(SQLScripts.keys())
    print(SQLScripts['create_database'])

    print(SQLScripts[SQLScripts.keys()[0]])

    print(SQLScripts.to_dict())
    print(SQLScripts)
