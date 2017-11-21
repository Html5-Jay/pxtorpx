import sublime
import sublime_plugin
import re
import time
import os

SETTINGS = {}
lastCompletion = {"needFix": False, "value": None, "region": None}

def plugin_loaded():
    init_settings()

def init_settings():
    get_settings()
    sublime.load_settings('cssrpx.sublime-settings').add_on_change('get_settings', get_settings)

def get_settings():
    settings = sublime.load_settings('cssrpx.sublime-settings')
    SETTINGS['px_to_rpx'] = settings.get('px_to_rpx', 40)
    SETTINGS['max_rpx_fraction_length'] = settings.get('max_rpx_fraction_length', 6)
    SETTINGS['available_file_types'] = settings.get('available_file_types', ['.wxss'])

def get_setting(view, key):
    return view.settings().get(key, SETTINGS[key]);

class CssRpxCommand(sublime_plugin.EventListener):
    def on_text_command(self, view, name, args):
        if name == 'commit_completion':
            view.run_command('replace_rpx')
        return None

    def on_query_completions(self, view, prefix, locations):

        fileName, fileExtension = os.path.splitext(view.file_name())
        if not fileExtension.lower() in get_setting(view, 'available_file_types'):
            return []

        lastCompletion["needFix"] = False
        location = locations[0]
        snippets = []

        match = re.compile("([\d.]+)p(x)?").match(prefix)
        if match:
            lineLocation = view.line(location)
            line = view.substr(sublime.Region(lineLocation.a, location))
            value = match.group(1)
            
            segmentStart = line.rfind(" ", 0, location)
            if segmentStart == -1:
                segmentStart = 0
            segmentStr = line[segmentStart:location]

            segment = re.compile("([\d.])+" + value).search(segmentStr)
            if segment:
                value = segment.group(0)
                start = lineLocation.a + segmentStart + 0 + segment.start(0)
                lastCompletion["needFix"] = True
            else:
                start = location

            rpxValue = round(float(value) / get_setting(view, 'px_to_rpx'), get_setting(view, 'max_rpx_fraction_length'))

            lastCompletion["value"] = str(rpxValue) + 'rpx'
            lastCompletion["region"] = sublime.Region(start, location)

            snippets += [(value + 'px ->rpx(' + str(get_setting(view, 'px_to_rpx')) + ')', str(rpxValue) + 'rpx;')]

        return snippets

class ReplaceRpxCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        needFix = lastCompletion["needFix"]
        if needFix == True:
            value = lastCompletion["value"]
            region = lastCompletion["region"]
            self.view.replace(edit, region, value)
            self.view.end_edit(edit)
