'''
An application to display and edit a configuration file that is stored in yaml format.

The configuration is loaded as a dictionary, and the app (using textual) displays the configuration
one key and value at a time, allowing the user to edit the value, and add/delete keys.

The configuration is saved back to the file when the user exits the app.
'''

import os
import re

from textual.app import App, ComposeResult
from textual.message import Message
from textual.validation import Validator, ValidationResult
from textual.widgets import Input, Header, Button
from textual.containers import HorizontalGroup, VerticalScroll

import yaml

class Config(dict):
    '''
    A simple subclass of a dict to hold the configuration data,
    that also handles mangling and unmangling the data to and from
    yaml format.

    For convenience, all the string keys are stored as object attributes.

    Usage:
    ```
    config = Config.load('config.yaml')

    '''

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for key, value in self.items():
            self[key] = value
            
    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if isinstance(key, str):
            setattr(self, re.sub(r'\s+', '_', key), value)

    def __delitem__(self, key):
        super().__delitem__(key)
        delattr(self, key)
    
    def save(self, path: os.PathLike) -> None:
        with open(path, 'w') as file:
            for key, value in self.items():
                if isinstance(value, str):
                    yaml.dump({key: self._mangle(value)}, file)
                else:
                    yaml.dump({key: value}, file)
    
    @classmethod
    def load(cls, path: os.PathLike) -> 'Config':
        cfg = cls()
        with open(path, 'r') as file:
            data = yaml.safe_load(file)
            for key, value in data.items():
                if isinstance(value, str):
                    cfg[key] = cfg._unmangle(value)
                else:
                    cfg[key] = value
        return cfg

    def _mangle(self, value: str) -> str:
        return value[::-1]
    
    def _unmangle(self, value: str) -> str:
        return value[::-1]


class TopBar(Header):
    DEFAULT_CSS = '''
    TopBar {
        height: 3;
        dock: top;
        background: $secondary
    }
    '''

class BottomBar(HorizontalGroup):
    DEFAULT_CSS = '''
    BottomBar {
        height: 3;
        dock: bottom;
        background: $panel;

        content-align: center middle;
    }
    '''

class Row(HorizontalGroup):
    DEFAULT_CSS = '''
    Row {
        width: 100%;
        padding: 1;
        border: solid $boost;
    }
    '''
    def __init__(self, k: str, v: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.k = Input(k, id=k, classes="keystr")
        self.v = Input(v, id=f'{k}_value', classes="valuestr")
    
    def compose(self) -> ComposeResult:
        yield self.k
        yield self.v

class QuitButton(Button):

    class Pressed(Message):
        def __init__(self) -> None:
            super().__init__()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def on_click(self) -> None:
        self.post_message(self.Pressed())
    
class SaveButton(Button):
    
    class Pressed(Message):
        def __init__(self) -> None:
            super().__init__()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def on_click(self) -> None:
        self.post_message(self.Pressed())


class AddRowButton(Button):
    class Pressed(Message):
        def __init__(self) -> None:
            super().__init__()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def on_click(self) -> None:
        self.post_message(self.Pressed())


class GoodFileNameValidator(Validator):
    def validate(self, value: str) -> ValidationResult:
        def is_valid_filename(fn: str) -> bool:
            if re.match(r'^[\w\-. ]+$', fn) is None:
                return False
            return os.path.exists(os.path.dirname(fn))
        return self.success() if is_valid_filename(value) else self.failure('Invalid filename or path.')


class Configurator(App):
    DEFAULT_CSS = '''
    .keystr {
        width: 25%;
    }
    .valuestr {
        width: 75%;
    }
    HorizontalGroup {
        content-align: center middle;
    }
    '''
    async def on_load(self) -> None:
        self.config = Config.load('config.yaml')
        self.keys = list(self.config.keys())
        self.index = 0

    def compose(self) -> ComposeResult:
        keys = [
            Row(key, self.config.get(key, ''))
            for key in self.keys
        ]
        with TopBar(show_clock=True, id='TopBar'):
            yield Input(
                'config.yaml',
                placeholder='config_filename.yaml',
                id='config_filename',
                validators=[GoodFileNameValidator(),],
                valid_empty=False,
                tooltip='Enter the filename to save the configuration to.',)
        
        with VerticalScroll():
            for key in keys:
                yield key
            yield AddRowButton('+', variant='default', name='add_row_button' )
        
        with BottomBar(id='BottomBar'):
            with HorizontalGroup():
                yield SaveButton('Save', variant='success', name='save_button')
                yield QuitButton('Quit', variant='primary', name='quit_button')

    def on_quit_button_pressed(self, message: QuitButton.Pressed) -> None:
        self.on_save_button_pressed(SaveButton.Pressed(), notify=False)
        self.exit()

    def on_save_button_pressed(self, message: SaveButton.Pressed, notify: bool=True) -> None:
        fn = self.query_one('#config_filename').value
        
        self.config = Config()
        self.config.update({
            row.k.value: row.v.value
            for row in self.query('Row')
            if not row.k.value == 'new_key'
        })
        self.keys = list(self.config.keys())
        self.config.save(fn)

        if notify:
            self.notify(f'Configuration saved to {fn} successfully.', title='Saved', timeout=3)

    def on_add_row_button_pressed(self, message: AddRowButton.Pressed) -> None:
        self.on_save_button_pressed(SaveButton.Pressed(), notify=False)
        self.keys.append('new_key')
        self.refresh(recompose=True)

if __name__ == '__main__':
    app = Configurator()
    app.run()