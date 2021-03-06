from sublime_db.core.typecheck import List, Callable, Optional

import os
import sublime

from sublime_db import ui, core

from .variable_component import (VariableComponent,
                                 Variable,
                                 VariableState,
                                 VariableComponent
                                 )
from .layout import console_panel_width

ERROR = 1
OUTPUT = 1 << 1
TEXT = 1 << 2
NONE = 1 << 3


class ConsoleItem (ui.Block):
	def __init__(self, kind: int, text: str, variable: Optional[Variable]):
		super().__init__()
		self.kind = kind
		self.text = text
		self.variable = variable

	def render(self) -> ui.Block.Children:
		width = console_panel_width(self.layout)
		if self.variable:
			return [VariableComponent(self.variable)]
		if self.kind == TEXT:
			return [
				ui.block(ui.Label(self.text, width=width, align=0, color='secondary'))
			]
		if (self.kind == OUTPUT) or (self.kind == NONE):
			return [
				ui.block(ui.Label(self.text, width=width, align=0, color='primary'))
			]
		if self.kind == ERROR:
			return [
				ui.block(ui.Label(self.text, width=width, align=0, color='red'))
			]
		assert None, "expected type..."


class ConsolePanel (ui.Block):
	def __init__(self, on_click: Callable[[], None]):
		super().__init__()
		self.items = [] #type: List[ui.Block]
		self.text = [] #type: List[str]
		self.on_click = on_click
		self.filter = ERROR | OUTPUT | TEXT | NONE

	def change_filter(self, index: int = 0) -> None:
		core.run(self.change_filter_async(sublime.active_window(), index))

	@core.async
	def change_filter_async(self, window, index) -> core.awaitable[None]:
		names = ["-- All -- ", "output: debugger", "output: program", "output: other"]
		masks = [
			(ERROR | OUTPUT | TEXT | NONE),
			(TEXT),
			(ERROR | OUTPUT),
			(NONE)
		]
		for i in range(0, 4):
			if self.filter & masks[i]:
				names[i] += "  ✓"

		selected_index = yield from core.sublime_show_quick_panel_async(window, names, index)
		if selected_index < 0:
			return

		if selected_index == 0:
			self.filter = masks[0]
		else:
			self.filter ^= masks[selected_index]

		self.change_filter(selected_index)
		self.dirty()

	def get_text(self) -> str:
		return ''.join(self.text)

	def open_in_view(self) -> None:
		file = sublime.active_window().new_file()
		file.run_command('append', {
                    'characters': self.get_text(),
                 			'scroll_to_end': True
		})

	def AddVariable(self, variable: Variable) -> None:
		self.text.append(variable.name)
		self.text.append(' = ')
		self.text.append(variable.value)

		item = ConsoleItem(OUTPUT, "", variable)
		self.items.append(item)
		self.dirty()

	def Add(self, text: str) -> None:
		self.text.append(text)
		for line in reversed(text.rstrip('\n').split('\n')):
			item = ConsoleItem(TEXT, line, None)
			self.items.append(item)
		self.dirty()

	def AddOutputOther(self, text: str) -> None:
		self.text.append(text)
		for line in reversed(text.rstrip('\n').split('\n')):
			item = ConsoleItem(NONE, line, None)
			self.items.append(item)
		self.dirty()

	def AddStdout(self, text: str) -> None:
		self.text.append(text)
		for line in reversed(text.rstrip('\n').split('\n')):
			item = ConsoleItem(OUTPUT, line, None)
			self.items.append(item)
		self.dirty()

	def AddStderr(self, text: str) -> None:
		self.text.append(text)
		for line in reversed(text.rstrip('\n').split('\n')):
			item = ConsoleItem(ERROR, line, None)
			self.items.append(item)
		self.dirty()

	def clear(self) -> None:
		self.items.clear()
		self.text.clear()
		self.dirty()

	def render(self) -> ui.Block.Children:
		count = int(self.layout.height() / 1.65)
		items = []

		for item in reversed(self.items):
			if len(items) >= count:
				break
			if item.kind & self.filter:
				items.append(item)
		items.reverse()
		items.append(ui.Button(self.on_click, items=[
			ui.Img(ui.Images.shared.right),
		]))
		return [
			ui.Table(items=items)
		]


class ConsoleVariable (ui.Block):
	def __init__(self, variable: Variable) -> None:
		super().__init__()
		self.variable = variable

	def render(self) -> ui.Block.Children:
		return [
			VariableComponent(self.variable)
		]
