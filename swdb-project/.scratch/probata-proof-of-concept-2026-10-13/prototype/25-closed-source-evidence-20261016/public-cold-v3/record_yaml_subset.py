"""2026-10-16 ET. Strict no-tag/no-anchor reader for yamlio's JSON-shaped output.

Independent observer only. Unknown YAML syntax refuses; never execute a loader.
The emitting yamlio source disables aliases and uses literal multiline strings.
"""
import json
import math
import re


def need(ok, message):
    if not ok:
        raise ValueError(message)


def scalar(text):
    text = text.strip()
    need(text and not text.startswith(('!', '&', '*', '>', '|', '?', '%', '#')), 'unsupported YAML scalar syntax')
    if text.startswith('"'):
        value = json.loads(text)
        need(isinstance(value, str), 'quoted YAML scalar is not text')
        return value
    if text.startswith("'"):
        need(len(text) >= 2 and text.endswith("'"), 'unclosed single quoted scalar')
        body = text[1:-1]
        need("'" not in body.replace("''", ''), 'unpaired YAML quote')
        return body.replace("''", "'")
    if text in ('null', '~'):
        return None
    if text in ('true', 'false'):
        return text == 'true'
    need(text.lower() not in ('yes', 'no', 'on', 'off', '.nan', '.inf', '+.inf', '-.inf', 'true', 'false', 'null')
         and not re.fullmatch(r'[-+]?0(?:[box][0-9a-fA-F_]+|[0-9_]+)', text)
         and not re.fullmatch(r'[-+]?[0-9]+(?::[0-9]+)+(?:\.[0-9]*)?', text),
         'noncanonical YAML implicit scalar')
    if re.fullmatch(r'-?(?:0|[1-9][0-9]*)', text):
        return int(text)
    if re.fullmatch(r'-?(?:[0-9]+\.[0-9]*|\.[0-9]+)(?:[eE][-+]?[0-9]+)?', text):
        value = float(text)
        need(math.isfinite(value), 'nonfinite YAML number')
        return value
    need(not re.fullmatch(r'[-+]?(?:[0-9][0-9_]*(?:\.[0-9_]*)?(?:[eE][-+]?[0-9]+)?|\.[0-9_]+(?:[eE][-+]?[0-9]+)?)',text),
         'noncanonical YAML numeric scalar')
    need(not text.startswith(('[', '{')) and ' #' not in text and ': ' not in text, 'unsupported plain YAML scalar')
    return text


def flow(text):
    index = 0
    def space():
        nonlocal index
        while index < len(text) and text[index].isspace():
            index += 1
    def atom(key=False):
        nonlocal index
        space(); start = index
        need(index < len(text), 'missing flow value')
        if text[index] in "\"'":
            quote = text[index]; index += 1
            while index < len(text):
                if text[index] == quote:
                    if quote == "'" and text[index:index+2] == "''":
                        index += 2; continue
                    index += 1; break
                if quote == '"' and text[index] == '\\':
                    index += 2
                else:
                    index += 1
            return scalar(text[start:index])
        if text[index] in '[{':
            opener = text[index]; closer = ']' if opener == '[' else '}'; index += 1
            result = [] if opener == '[' else {}
            space()
            if index < len(text) and text[index] == closer:
                index += 1; return result
            while True:
                value = atom(opener == '{')
                if opener == '[':
                    result.append(value)
                else:
                    need(isinstance(value, str) and value not in result, 'flow key duplicate/type')
                    space(); need(index < len(text) and text[index] == ':', 'flow mapping separator'); index += 1
                    result[value] = atom()
                space(); need(index < len(text), 'unclosed YAML flow value')
                if text[index] == closer:
                    index += 1; return result
                need(text[index] == ',', 'flow item separator'); index += 1
        while index < len(text) and text[index] not in (',]}:' if key else ',]}'):
            index += 1
        return scalar(text[start:index])
    value = atom(); space(); need(index == len(text), 'trailing flow YAML bytes')
    return value


class Reader:
    def __init__(self, raw):
        self.lines = raw.decode('utf-8').splitlines()
        need(not any('\t' in line[:len(line)-len(line.lstrip())] for line in self.lines), 'YAML indentation tab')
        self.at = 0
        self.nodes = 0
    def skip(self):
        while self.at < len(self.lines) and not self.lines[self.at].strip():
            self.at += 1
    def indentation(self):
        return len(self.lines[self.at]) - len(self.lines[self.at].lstrip(' '))
    def split(self, text):
        quote = None; depth = 0; at = 0
        while at < len(text):
            ch = text[at]
            if quote:
                if ch == quote:
                    if quote == "'" and text[at:at+2] == "''":
                        at += 2; continue
                    quote = None
                elif quote == '"' and ch == '\\':
                    at += 2; continue
            elif ch in "\"'":
                quote = ch
            elif ch in '[{': depth += 1
            elif ch in ']}': depth -= 1
            elif ch == ':' and not depth and (at+1 == len(text) or text[at+1].isspace()):
                return text[:at], text[at+1:].lstrip()
            at += 1
        return None
    def value(self, value, indent):
        if re.fullmatch(r'\|[1-9]?[+-]?', value):
            # yamlio emits a literal block for every actual newline-bearing str.
            match = re.fullmatch(r'\|([1-9]?)([+-]?)', value); indicator, chomp = match.groups()
            first = self.at
            probe = first
            while probe < len(self.lines) and not self.lines[probe].strip(): probe += 1
            base = indent + int(indicator) if indicator else (len(self.lines[probe])-len(self.lines[probe].lstrip(' ')) if probe < len(self.lines) else indent+2)
            need(base > indent, 'literal block indentation')
            parts = []
            while self.at < len(self.lines):
                line = self.lines[self.at]
                if line.strip() and len(line)-len(line.lstrip(' ')) < base: break
                parts.append(line[base:] if line.strip() else '')
                self.at += 1
            text = '\n'.join(parts)+'\n'
            if chomp == '-': return text.rstrip('\n')
            if chomp == '+': return text
            return text.rstrip('\n')+'\n'
        if not value:
            self.skip()
            if self.at == len(self.lines) or self.indentation() < indent:
                return None
            if self.indentation() == indent and not self.lines[self.at].lstrip().startswith('- '):
                return None
            return self.block(self.indentation())
        # Long plain/quoted/flow strings are folded by the fixed width emitter.
        while self.at < len(self.lines):
            line = self.lines[self.at]
            if not line.strip(): break
            amount = len(line)-len(line.lstrip(' '))
            if amount <= indent: break
            value += ' '+line.strip(); self.at += 1
        return flow(value) if value.startswith(('[', '{')) else scalar(value)
    def block(self, indent):
        self.nodes += 1; need(self.nodes < 200000, 'YAML node budget')
        self.skip(); need(self.at < len(self.lines) and self.indentation() == indent, 'YAML block indentation')
        sequence = self.lines[self.at][indent:].startswith('- ')
        result = [] if sequence else {}
        while self.at < len(self.lines):
            self.skip()
            if self.at == len(self.lines) or self.indentation() < indent: break
            if self.indentation() != indent: break
            text = self.lines[self.at][indent:]
            if text.startswith('- ') != sequence: break
            self.at += 1
            if sequence:
                tail = text[2:]; pair = self.split(tail)
                if pair:
                    key, value = pair; key = scalar(key); need(isinstance(key,str), 'YAML mapping key')
                    item = {key:self.value(value,indent+2)}
                    self.skip()
                    if self.at < len(self.lines) and self.indentation() == indent+2:
                        rest = self.block(indent+2)
                        need(isinstance(rest,dict) and not set(item).intersection(rest), 'YAML list mapping duplicate')
                        item.update(rest)
                    result.append(item)
                else: result.append(self.value(tail,indent))
            else:
                pair = self.split(text); need(pair is not None, 'YAML mapping colon')
                key, value = pair; key = scalar(key)
                need(isinstance(key,str) and key not in result, 'YAML mapping duplicate/key type')
                result[key] = self.value(value,indent)
        return result


def loads(raw):
    reader = Reader(raw); reader.skip()
    need(reader.at < len(reader.lines), 'empty YAML document')
    result = reader.block(reader.indentation()); reader.skip()
    need(reader.at == len(reader.lines), 'unconsumed or unsupported YAML syntax')
    return result
