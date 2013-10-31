"""
Package File Search
Licensed under MIT
Copyright (c) 2012 Isaac Muse <isaacmuse@gmail.com>

Example Commands:
    //////////////////////////////////
    // Package File Search Commands
    //////////////////////////////////
    {
        "caption": "Package File Search: Menu",
        "command": "get_package_files_menu",
        "args": {
            "pattern_list": [
                {"caption": "Settings Files",        "search": {"pattern": "*.sublime-settings", "regex": false}},
                {"caption": "Keymap Files",          "search": {"pattern": "*.sublime-keymap",   "regex": false}},
                {"caption": "Command Files",         "search": {"pattern": "*.sublime-commands", "regex": false}},
                {"caption": "Readme Files",          "search": {"pattern": "*readme*",           "regex": false}},
                {"caption": "Language Syntax Files", "search": {"pattern": "*tmLanguage",        "regex": false}},
                {"caption": "Snippet Files",         "search": {"pattern": "*.sublime-snippet",  "regex": false}},
                {"caption": "Preference Files",      "search": {"pattern": "*.tmPreferences",    "regex": false}},
                {"caption": "Color Scheme Files",    "search": {"pattern": "*.tmTheme",          "regex": false}},
                {"caption": "Theme Files",           "search": {"pattern": "*.sublime-theme",    "regex": false}},
                {"caption": "Python Source Files",   "search": {"pattern": "*.py",               "regex": false}},
                {"caption": "Sublime Menues",        "search": {"pattern": "*.sublime-menu",     "regex": false}}
            ]
        }
    },
    {
        "caption": "Package false Search: Menu (find false)",
        "command": "get_package_files_menu",
        "args": {
            "pattern_list": [
                {"caption": "Settings Files",        "search": {"pattern": "*.sublime-settings", "regex": false}},
                {"caption": "Keymap Files",          "search": {"pattern": "*.sublime-keymap",   "regex": false}},
                {"caption": "Command Files",         "search": {"pattern": "*.sublime-commands", "regex": false}},
                {"caption": "Readme Files",          "search": {"pattern": "*readme*",           "regex": false}},
                {"caption": "Language Syntax Files", "search": {"pattern": "*tmLanguage",        "regex": false}},
                {"caption": "Snippet Files",         "search": {"pattern": "*.sublime-snippet",  "regex": false}},
                {"caption": "Preference Files",      "search": {"pattern": "*.tmPreferences",    "regex": false}},
                {"caption": "Color Scheme Files",    "search": {"pattern": "*.tmTheme",          "regex": false}},
                {"caption": "Theme Files",           "search": {"pattern": "*.sublime-theme",    "regex": false}},
                {"caption": "Python Source Files",   "search": {"pattern": "*.py",               "regex": false}},
                {"caption": "Sublime Menues",        "search": {"pattern": "*.sublime-menu",     "regex": false}}
            ],
            "find_all": true
        }
    },
    {
        "caption": "Package false Search: Input Search Pattern",
        "command": "get_package_files_input"
    },
    {
        "caption": "Package File Search: Input Search Pattern (find all)",
        "command": "get_package_files_input",
        "args": {"find_all": true}
    },
"""

import sublime
import sublime_plugin
from os.path import join, isdir, normpath, dirname, basename, splitext, exists
from os import listdir, walk
from fnmatch import fnmatch
import re
import zipfile


def sublime_package_paths():
    return [sublime.installed_packages_path(), join(dirname(sublime.executable_path()), 'Packages')]


class WriteArchivedPackageContentCommand(sublime_plugin.TextCommand):
    bfr = None
    def run(self, edit):
        cls = WriteArchivedPackageContentCommand
        if cls.bfr is not None:
            self.view.set_read_only(False)
            self.view.set_scratch(True)
            self.view.replace(edit, sublime.Region(0, self.view.size()), cls.bfr)
            sels = self.view.sel()
            sels.clear()
            sels.add(0)
            cls.bfr = None
            self.view.set_read_only(True)


class GetPackageFilesInputCommand(sublime_plugin.WindowCommand):
    def find_pattern(self, pattern, find_all=False):
        regex = False
        if pattern != "":
            m = re.match(r"^[ \t]*`(.*)`[ \t]*$", pattern)
            if m != None:
                regex = True
                pattern = m.group(1)
            self.window.run_command(
                "get_package_files",
                {
                    "pattern": pattern,
                    "regex": regex,
                    "find_all": find_all
                }
            )

    def run(self, find_all=False):
        self.window.show_input_panel(
            "File Pattern: ",
            "",
            lambda x: self.find_pattern(x, find_all=find_all),
            None,
            None
        )


class GetPackageFilesMenuCommand(sublime_plugin.WindowCommand):
    def find_files(self, value, patterns, find_all):
        if value > -1:
            pat = patterns[value]
            sublime.set_timeout(
                lambda: self.window.run_command(
                    "get_package_files",
                    {
                        "pattern": pat["pattern"],
                        "regex": pat.get("regex", False),
                        "find_all": find_all
                    }
                ),
                100
            )

    def run(self, pattern_list=[], find_all=False):
        patterns = []
        types = []
        for item in pattern_list:
            patterns.append(item["search"])
            types.append(item["caption"])
        if len(types) == 1:
            self.find_files(0, patterns, find_all)
        elif len(types):
            self.window.show_quick_panel(
                types,
                lambda x: self.find_files(x, patterns=patterns, find_all=find_all)
            )

class GetColorSchemeFileCommand(GetPackageFilesCommand):
    def preview_color(self, value, settings):
        if value != -1:
            sublime.load_settings("Preferences.sublime-settings").set("color_scheme", settings[value])

    def set_color_scheme(self, value, settings):
        if value != -1:
            sublime.load_settings("Preferences.sublime-settings").set("color_scheme", settings[value])
        else:
            if self.current_color_scheme is not None:
                sublime.load_settings("Preferences.sublime-settings").set("color_scheme", self.current_color_scheme)

    def find(self, pattern, regex):
        resources = []
        if not regex:
            resources = sublime.find_resources(pattern)
        else:
            temp = sublime.find_resources("*")
            for t in temp:
                if re.match(pattern, t, re.IGNORECASE) != None:
                    resources.append(t)

        self.window.show_quick_panel(
            resources,
            lambda x: self.set_color_scheme(x, settings=resources),
            0,
            0,
            lambda x: self.preview_color(x, settings=resources)
        )

    def run(self, pattern=None, regex=False, find_all=False):
        pattern = "*.tmTheme"
        regex = False
        find_all = False
        self.current_color_scheme = sublime.load_settings("Preferences.sublime-settings").get("color_scheme")
        self.find(pattern, regex)


class GetPackageFilesCommand(sublime_plugin.WindowCommand):
    def open_file_quick(self, value, settings):
        if value > -1:
            self.window.run_command("open_file", {"file": settings[value].replace("Packages", "${packages}", 1)})

    def find_files(self, files, pattern, settings, regex):
        for f in files:
            if regex:
                if re.match(pattern, f[0], re.IGNORECASE) != None:
                    settings.append([f[0].replace(self.packages, "").lstrip("\\").lstrip("/"), f[1]])
            else:
                if fnmatch(f[0], pattern):
                    settings.append([f[0].replace(self.packages, "").lstrip("\\").lstrip("/"), f[1]])

    def walk(self, settings, plugin, pattern, regex=False):
        for base, dirs, files in walk(plugin):
            files = [(join(base, f), "Packages") for f in files]
            self.find_files(files, pattern, settings, regex)

    def open_file(self, value, settings):
        if value > -1:
            if value >= self.zipped_idx:
                self.open_zip_file(settings[value][0])
            else:
                self.window.open_file(join(self.packages, settings[value][0]))

    def open_zip_file(self, fn):
        file_name = None
        zip_package = None
        zip_file = None
        for zp in sublime_package_paths():
            items = fn.replace('\\', '/').split('/')
            zip_package = items.pop(0)
            zip_file = '/'.join(items)
            if exists(join(zp, zip_package)):
                zip_package = join(zp, zip_package)
                file_name = join(zp, fn)
                break

        if file_name is not None:
            with zipfile.ZipFile(zip_package, 'r') as z:
                text = z.read(z.getinfo(zip_file))
                view = self.window.open_file(file_name)
                WriteArchivedPackageContentCommand.bfr = text.decode('utf-8').replace('\r', '')
                sublime.set_timeout(lambda: view.run_command("write_archived_package_content"), 0)


    def get_zip_packages(self, file_path, package_type):
        plugins = [(join(file_path, item), package_type) for item in listdir(file_path) if fnmatch(item, "*.sublime-package")]
        return plugins

    def search_zipped_files(self):
        plugins = []
        st_packages = sublime_package_paths()
        plugins += self.get_zip_packages(st_packages[0], "Installed")
        plugins += self.get_zip_packages(st_packages[1], "Default")
        return plugins

    def walk_zip(self, settings, plugin, pattern, regex):
        # psuedo_path = join(normpath(sublime.packages_path()), splitext(basename(plugin))[0])
        with zipfile.ZipFile(plugin[0], 'r') as z:
            zipped = [(join(basename(plugin[0]), normpath(fn)), plugin[1]) for fn in sorted(z.namelist())]
            self.find_files(zipped, pattern, settings, regex)

    def find_all(self, pattern, regex=False):
        self.packages = normpath(sublime.packages_path())
        settings = []
        plugins = [join(self.packages, item) for item in listdir(self.packages) if isdir(join(self.packages, item))]
        for plugin in plugins:
            self.walk(settings, plugin, pattern.strip(), regex)

        self.zipped_idx = len(settings)

        zipped_plugins = self.search_zipped_files()
        for plugin in zipped_plugins:
            self.walk_zip(settings, plugin, pattern.strip(), regex)

        self.window.show_quick_panel(
            settings,
            lambda x: self.open_file(x, settings=settings)
        )

    def find(self, pattern, regex):
        resources = []
        if not regex:
            resources = sublime.find_resources(pattern)
        else:
            temp = sublime.find_resources("*")
            for t in temp:
                if re.match(pattern, t, re.IGNORECASE) != None:
                    resources.append(t)

        self.window.show_quick_panel(
            resources,
            lambda x: self.open_file_quick(x, settings=resources)
        )

    def run(self, pattern, regex=False, find_all=False):
        if not find_all:
            self.find(pattern, regex)
        else:
            self.find_all(pattern, regex)
