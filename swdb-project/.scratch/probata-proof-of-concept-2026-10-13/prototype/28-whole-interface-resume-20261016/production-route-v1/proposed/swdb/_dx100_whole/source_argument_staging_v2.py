"""2026-10-16 ET. Inert checked argument/CPU projection; stdlib only.

No compiler, project import, source admission or receiver-state constructor.
The caller supplies an actual single-TU observation through the reviewed binder.
This first slice accepts pure scalar/local/descriptor arguments; CPU accesses are
separate source-owned statements. General C++ expression/control lowering stays
with the scoped original lowerer, including its original UB/assertion properties.
"""
import hashlib
import json
from pathlib import Path
import re

BINDER_SHA = '217cdda6ca8eaea99526010f2c379dad963ca81c18c79322ce02ab8cc9296ed8'
DISPATCH_SHA = 'd05d3ba716af2d88703636ffbf57bf0834acd5e59ee7ce3aebe0a72648a8b703'
TYPE_KEYS = ('uint32_t', 'int32_t', 'float', 'uint64_t', 'int64_t', 'double')
SUFFIX = ('u32', 'i32', 'f32', 'u64', 'i64', 'f64')
SCALARS = {'bool': '_Bool', 'signed char': 'signed char', 'unsigned char': 'unsigned char',
    'short': 'short', 'unsigned short': 'unsigned short', 'int': 'int', 'unsigned int': 'unsigned int',
    'long': 'long', 'unsigned long': 'unsigned long', 'long long': 'long long',
    'unsigned long long': 'unsigned long long', 'float': 'float', 'double': 'double',
    'DataType': 'uint8_t', 'Operation_t': 'int'}
SMALL_OFFSETS = {'bool', 'signed char', 'unsigned char', 'short', 'unsigned short', 'int', 'unsigned int'}
BINARY = {'+', '-', '*', '/', '%', '&', '|', '^', '<<', '>>', '==', '!=', '<', '<=', '>', '>=', '&&', '||'}


class Refused(ValueError):
    pass


def need(ok, message):
    if not ok: raise Refused(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def kind_type(node):
    typ = node.get('type', {})
    need(isinstance(typ, dict) and isinstance(typ.get('qualType'), str), 'actual compiler type required')
    for field in ('qualType', 'desugaredQualType'):
        if field in typ:
            need(isinstance(typ[field], str) and not re.search(r'\bvolatile\b', typ[field]), 'volatile source reads outside staging grammar')
    return ' '.join(typ.get('desugaredQualType', typ['qualType']).split())


class Stager:
    """Fresh local identity/argument projection, without arbitrary C callbacks.

    `live_local_ids` is the scoped lowerer's current definitely initialized/live
    environment; emitting a registration never makes a local live or initialized.
    Actual compiler/full-TU, local lifetime/dominance and original source RTE are
    separate obligations. All generated names are internal deterministic names.
    """
    def __init__(self, api, dispatch, tu, *, caller, source_path, source_text, declarations, abi,
                 atlas, live_local_ids, thread='owned_thread'):
        for module, pin in ((api, BINDER_SHA), (dispatch, DISPATCH_SHA)):
            need(hashlib.sha256(Path(module['__file__']).read_bytes()).hexdigest() == pin, 'exact reviewed source modules required')
        api['validate_abi'](abi)
        need(Path(source_path).read_bytes() == source_text.encode('ascii'), 'exact physical ASCII caller required')
        need(type(live_local_ids) is set and all(isinstance(item, str) for item in live_local_ids), 'explicit scoped live/initialized local IDs required')
        self.api, self.dispatch, self.tu = api, dispatch, tu
        self.tu_pin = digest(tu)
        self.source = dict(caller=caller, source_path=source_path, source_text=source_text, declarations=declarations, abi=abi)
        self.abi, self.thread, self.locals, self.serial = abi, dispatch['identifier'](thread), {}, 0
        self.live = set(live_local_ids)
        self.atlas = dispatch['prepare_atlas']([{key: row[key] for key in ('object_id','guest_base','physical_base','extent','dtype','source_pin')}
                                              for row in atlas['objects']])
        need(self.atlas == atlas, 'fresh complete ordinary atlas required')
        callers = []
        def walk(node):
            if node.get('kind') == 'FunctionDecl' and node.get('mangledName') == caller: callers.append(node)
            for child in node.get('inner', []):
                if isinstance(child, dict): walk(child)
        walk(tu)
        need(len(callers) == 1, 'one source-owned caller required')
        self.owner = callers[0]
        loc = self.owner.get('loc', {})
        need(loc.get('_file', loc.get('file')) == str(Path(source_path).resolve()), 'source owner physical file required')
        self.declarations = {}
        def local_walk(node):
            if node is not self.owner and node.get('kind') in {'FunctionDecl','LambdaExpr'}: return
            if node.get('kind') == 'VarDecl':
                ident = node.get('id')
                need(isinstance(ident, str) and ident and ident not in self.declarations, 'unique same-caller local declaration ID required')
                self.declarations[ident] = node
            for child in node.get('inner', []):
                if isinstance(child, dict): local_walk(child)
        local_walk(self.owner)
        self.enum_values = {}
        headers = {Path(row['header_path']).name: row for row in declarations}
        def enums(node):
            name = node.get('name')
            if node.get('kind') == 'EnumDecl' and name in {'Operation_t','DataType'}:
                record = headers['MAA.hpp' if name == 'Operation_t' else 'MAA_gem5.hpp']
                path = Path(record['header_path']);raw = path.read_bytes()
                need(hashlib.sha256(raw).hexdigest() == record['header_sha256'], 'enum physical source pin changed')
                loc = node.get('loc', {})
                need(loc.get('_file',loc.get('file')) == str(path), 'enum must belong to original pinned header')
                start,end = api['_span'](node)
                spelling = raw[start:end].decode('ascii')
                expected = re.search(r'enum class '+name+r'(?: : uint8_t)?\s*\{[^}]*\}',raw.decode('ascii'))
                need(expected and spelling == expected[0], 'enum exact source declaration span required')
                wanted = []
                for part in spelling[spelling.index('{')+1:-1].split(','):
                    match = re.fullmatch(r'\s*([A-Za-z_]\w*)(?:\s*=\s*([0-9]+))?\s*',part)
                    need(match, 'closed literal original enum declaration required')
                    wanted.append((match[1],int(match[2]) if match[2] else (wanted[-1][1]+1 if wanted else 0)))
                children = node.get('inner', [])
                need(len(children) == len(wanted), 'enum complete original enumerator census required')
                for child,(enum_name,number) in zip(children,wanted):
                    ident = child.get('id')
                    need(child.get('kind') == 'EnumConstantDecl' and child.get('name') == enum_name
                         and isinstance(ident,str) and ident not in self.enum_values, 'unique actual enum identity required')
                    constants = child.get('inner', [])
                    if constants:
                        need(len(constants) == 1 and constants[0].get('kind') == 'ConstantExpr'
                             and constants[0].get('value') == str(number), 'enum observed constant differs from pinned source')
                    self.enum_values[ident] = (name,number)
            for child in node.get('inner', []):
                if isinstance(child,dict): enums(child)
        enums(tu)

    def _owned(self, node):
        need(digest(self.tu) == self.tu_pin and Path(self.source['source_path']).read_bytes() == self.source['source_text'].encode('ascii'),
             'selected source/TU changed after staging setup')
        found = []
        def walk(item):
            if item is node: found.append(item)
            for child in item.get('inner', []):
                if isinstance(child,dict): walk(child)
        walk(self.owner)
        need(len(found) == 1, 'CPU/local projection requires the actual same-caller TU node')

    def _ctype(self, text):
        if text.startswith('const '): text = text[6:]
        return SCALARS.get(text)

    def _dtype(self, text):
        need(text in self.abi['canonical_types'].values(), 'observed six-type pointer element required')
        return next(i for i,key in enumerate(TYPE_KEYS) if self.abi['canonical_types'][key] == text)

    def register_local(self, ident, *, ordinary_object=None):
        need(ident in self.declarations and ident not in self.locals, 'fresh source-owned local identity required')
        node = self.declarations[ident]
        self._owned(node)
        loc = node.get('loc', {})
        need(loc.get('_file',loc.get('file')) == str(Path(self.source['source_path']).resolve()), 'direct original local physical file required')
        begin,end = self.api['_span'](node)
        need(0 <= begin < end <= len(self.source['source_text']), 'direct original local span required')
        need(node.get('storageClass') not in {'static','extern'} and not node.get('tls'), 'automatic local only')
        need(not any(child.get('kind','').endswith('Attr') for child in node.get('inner', [])), 'attributed local refuses')
        typ = kind_type(node)
        array = re.fullmatch(r'(.+?)\s*\[([1-9][0-9]*)\]', typ)
        pointer = re.fullmatch(r'(?:const )?(.+?)\s*\*', typ)
        value = {'declaration_sha256': digest(node), 'source_type': typ, 'name': 'src_local_' + str(len(self.locals))}
        if array:
            dtype, extent = self._dtype(array[1]), int(array[2])
            expected = digest({'source_sha256': hashlib.sha256(self.source['source_text'].encode()).hexdigest(),
                               'caller': self.source['caller'], 'local_id': ident, 'declaration_sha256': digest(node)})
            found = [(index,row) for index,row in enumerate(self.atlas['objects']) if row['object_id'] == ordinary_object]
            need(len(found) == 1 and found[0][1]['source_pin'] == expected and found[0][1]['dtype'] == dtype
                 and found[0][1]['extent'] == extent, 'ordinary object exact source/type/extent/projection certificate required')
            value.update(category='pointer-descriptor', dtype=dtype, c_type='struct dws_pointer', object_index=found[0][0], extent=extent)
            value['ordinary_descriptor_initializer'] = 'dws_object_pointer('+str(found[0][0])+')'
        elif pointer:
            need(ordinary_object is None, 'pointer local is not an ordinary array allocation')
            value.update(category='pointer-descriptor', dtype=self._dtype(pointer[1]), c_type='struct dws_pointer')
        else:
            ctype = self._ctype(typ)
            need(ctype is not None and ordinary_object is None, 'exact observed scalar local required')
            value.update(category='exact-scalar', c_type=ctype)
        self.locals[ident] = value
        return dict(value)

    def _value(self, text, typ, category='exact-scalar', **extra):
        return dict(expression=text, source_type=typ, category=category, **extra)

    def expression(self, node):
        """Closed pure expression grammar; never accepts calls, memory reads or effects."""
        need(isinstance(node, dict), 'compiler expression object required')
        kind, children = node.get('kind'), node.get('inner', [])
        need(isinstance(children, list) and all(isinstance(child, dict) for child in children), 'exact expression children required')
        typ = kind_type(node)
        if kind == 'DeclRefExpr':
            if not children and node.get('referencedDecl', {}).get('kind') == 'EnumConstantDecl':
                ident = node['referencedDecl'].get('id')
                need(ident in self.enum_values and self.enum_values[ident][0] == typ, 'exact pinned same-TU enum constant required')
                return self._value('((' + self._ctype(typ) + ')' + str(self.enum_values[ident][1]) + ')',typ)
            need(not children and node.get('referencedDecl', {}).get('kind') == 'VarDecl', 'local variable reference required')
            ident = node['referencedDecl'].get('id')
            need(ident in self.locals and ident in self.live, 'local must be source-bound, live and definitely initialized')
            value = self.locals[ident]
            need(digest(self.declarations[ident]) == value['declaration_sha256'], 'registered local declaration changed')
            need(typ == value['source_type'], 'local reference type differs from declaration')
            return self._value(value['name'], typ, value['category'], dtype=value.get('dtype'))
        if kind == 'IntegerLiteral':
            need(not children and self._ctype(typ) and typ not in {'float','double','DataType','Operation_t'}
                 and isinstance(node.get('value'), str) and re.fullmatch(r'[0-9]+', node['value']), 'typed integer literal required')
            value = int(node['value'])
            need(value <= 2**64-1, 'bounded source integer literal')
            return self._value('((' + self._ctype(typ) + ')UINT64_C(' + str(value) + '))', typ)
        if kind == 'CXXBoolLiteralExpr':
            need(not children and typ == 'bool' and type(node.get('value')) is bool, 'actual bool literal required')
            return self._value('1' if node['value'] else '0',typ)
        if kind in {'ParenExpr', 'ConstantExpr'}:
            need(len(children) == 1, 'one pure wrapper child required')
            value = self.expression(children[0]);need(value['source_type'] == typ, 'wrapper type changed')
            return dict(value, expression='(' + value['expression'] + ')')
        if kind == 'ImplicitCastExpr':
            need(len(children) == 1 and node.get('castKind') in {'NoOp','LValueToRValue','IntegralCast','IntegralToFloating','FloatingCast','ArrayToPointerDecay','BitCast'}, 'closed source conversion required')
            value = self.expression(children[0]);cast = node['castKind']
            if value['category'] == 'pointer-descriptor':
                need(cast in {'NoOp','LValueToRValue','ArrayToPointerDecay','BitCast'} and (typ.endswith('*') or typ.endswith(' *')), 'descriptor-preserving pointer cast required')
                if cast == 'BitCast': need(typ in {'void *','const void *'}, 'pointer reinterpretation refuses')
                else: need(re.sub(r'\s*\*$', '', typ).removeprefix('const ') == self.abi['canonical_types'][TYPE_KEYS[value['dtype']]], 'pointer element type changed')
                return dict(value, source_type=typ)
            need(cast in {'NoOp','LValueToRValue','IntegralCast','IntegralToFloating','FloatingCast'} and self._ctype(typ), 'scalar source conversion required')
            return self._value('((' + self._ctype(typ) + ')(' + value['expression'] + '))', typ)
        if kind == 'UnaryOperator':
            need(len(children) == 1 and node.get('opcode') in {'+','-','!','~'}, 'pure unary operator required')
            value = self.expression(children[0]);need(value['category'] == 'exact-scalar' and self._ctype(typ), 'scalar unary operands required')
            return self._value('(' + node['opcode'] + '(' + value['expression'] + '))', typ)
        if kind == 'BinaryOperator':
            need(len(children) == 2 and node.get('opcode') in BINARY, 'pure binary operator required')
            left, right = map(self.expression, children);op = node['opcode']
            pointers = [value for value in (left,right) if value['category'] == 'pointer-descriptor']
            if pointers:
                need(len(pointers) == 1 and op in {'+','-'} and (op == '+' or pointers[0] is left), 'bounded pointer offset only')
                pointer = pointers[0];offset = right if pointer is left else left
                need(offset['source_type'] in SMALL_OFFSETS, 'at most 32-bit integral pointer offset required')
                need(re.sub(r'\s*\*$', '', typ).removeprefix('const ') == self.abi['canonical_types'][TYPE_KEYS[pointer['dtype']]], 'pointer arithmetic element type changed')
                sign = '-' if op == '-' else ''
                return self._value('dws_pointer_offset(' + pointer['expression'] + ',' + sign + '((int64_t)(' + offset['expression'] + ')))', typ,
                                   'pointer-descriptor', dtype=pointer['dtype'])
            need(self._ctype(typ), 'scalar binary result required')
            return self._value('((' + left['expression'] + ') ' + op + ' (' + right['expression'] + '))', typ)
        raise Refused('source expression is outside the closed staging grammar: ' + str(kind))

    def call(self, binding):
        need(digest(self.tu) == self.tu_pin and binding.get('caller_mangled') == self.source['caller'], 'original staging caller/TU changed')
        source = dict(self.source,call_range=binding.get('call_range'))
        fresh = self.api['recheck_binding'](binding, self.tu, **source)
        matches = []
        def walk(node):
            if node.get('kind') == 'CallExpr':
                try: direct_span = self.api['_span'](node)
                except self.api['Refused']: direct_span = None
                if direct_span == fresh['call_range']: matches.append(node)
            for child in node.get('inner', []):
                if isinstance(child, dict): walk(child)
        walk(self.owner);need(len(matches) == 1, 'one exact source-owned call required')
        plan = self.api['dispatch_plan'](fresh, self.source['declarations'], self.abi)
        lines, stages = [], []
        for index,(node,parameter) in enumerate(zip(matches[0]['inner'][1:],plan['source_arguments'])):
            if node.get('kind') == 'CXXDefaultArgExpr':
                value = self._value('-1','int')
            else: value = self.expression(node)
            expected = 'pointer-descriptor' if '*' in parameter['source_type'] else 'exact-scalar'
            need(value['category'] == expected, 'argument descriptor/scalar role differs from exact source parameter')
            name = 'src_arg_' + str(self.serial);self.serial += 1
            ctype = 'struct dws_pointer' if expected == 'pointer-descriptor' else self._ctype(value['source_type'])
            need(ctype, 'source argument concrete C type required')
            lines.append(ctype + ' ' + name + ' = ' + value['expression'] + ';')
            stages.append({'index': index,'ast_sha256': self.dispatch['digest'](node),'identifier':name,'model_type':expected})
        result = self.dispatch['bind_dispatch'](self.api,self.tu,binding=fresh,staged_arguments=stages,thread=self.thread,**source)
        return dict(result, staging_statements=lines, staging_grammar='closed pure scalar/local/descriptor v1',
                    source_RTE_and_local_lifetime_checks_required=True, receiver_state_binding_required=True,
                    harness_draw_plan_required=True, public_admission=False)

    def _access(self, node):
        need(node.get('kind') == 'ArraySubscriptExpr' and len(node.get('inner', [])) == 2, 'one rank-one source subscript required')
        begin,end=self.api['_span'](node)
        need(0 <= begin < end <= len(self.source['source_text']), 'direct original CPU source span required')
        for point in node['range'].values():
            need(point.get('_file',point.get('file')) == str(Path(self.source['source_path']).resolve()), 'CPU source physical file differs')
        pointer, index = map(self.expression, node['inner'])
        need(pointer['category'] == 'pointer-descriptor' and index['category'] == 'exact-scalar'
             and index['source_type'] in SMALL_OFFSETS, 'typed descriptor and small integral index required')
        dtype = pointer['dtype'];need(kind_type(node) == self.abi['canonical_types'][TYPE_KEYS[dtype]], 'source CPU scalar type differs from pointer element')
        return pointer,index,dtype

    def cpu_load(self, node):
        self._owned(node)
        pointer,index,dtype = self._access(node)
        return {'expression':'dws_cpu_load_' + SUFFIX[dtype] + '(' + self.thread + ',' + pointer['expression'] + ',(int64_t)(' + index['expression'] + '))',
            'source_access_sha256':digest(node),'source_range':self.api['_span'](node),'dtype':dtype,'access':'read','one_event':True,'public_admission':False}

    def cpu_store(self, assignment, *, discarded_statement):
        self._owned(assignment)
        need(discarded_statement is True and assignment.get('kind') == 'BinaryOperator' and assignment.get('opcode') == '='
             and len(assignment.get('inner', [])) == 2, 'standalone source assignment required')
        target,value_node = assignment['inner'];pointer,index,dtype = self._access(target)
        self.api['_span'](assignment)
        value = self.expression(value_node)
        need(value['category'] == 'exact-scalar' and value['source_type'] == self.abi['canonical_types'][TYPE_KEYS[dtype]], 'store exact source scalar conversion required')
        serial=self.serial;self.serial+=1
        rhs='src_store_'+str(serial);base='src_base_'+str(serial);offset='src_index_'+str(serial)
        return {'statements':[self._ctype(value['source_type'])+' '+rhs+' = '+value['expression']+';',
            'struct dws_pointer '+base+' = '+pointer['expression']+';', 'int64_t '+offset+' = (int64_t)('+index['expression']+');',
            'dws_cpu_store_'+SUFFIX[dtype]+'('+self.thread+','+base+','+offset+','+rhs+');'],
            'source_access_sha256':digest(assignment),'dtype':dtype,'access':'write','one_event':True,
            'assignment_order':'C++17 RHS before LHS; one final shared-model store','public_admission':False}

    def array_initializer(self, ident):
        """Project original C++ scalar aggregate initialization into shared cells.

        This changes payload only through original source writes. Object lifetime,
        local-allocation ownership and the initial receiver remain separate checked
        producer/harness obligations. No source declaration means no initializer.
        """
        need(ident in self.locals and 'object_index' in self.locals[ident], 'registered ordinary source array required')
        local,node=self.locals[ident],self.declarations[ident];self._owned(node)
        initializers=node.get('inner',[])
        need(len(initializers) == 1 and initializers[0].get('kind') == 'InitListExpr', 'one original aggregate initializer required')
        init=initializers[0];prefix=init.get('inner',[])
        need(isinstance(prefix,list), 'original initializer child list required')
        if 'array_filler' in init:
            filler=init['array_filler']
            need(not prefix and isinstance(filler,list) and filler and filler[0].get('kind') == 'ImplicitValueInitExpr', 'unambiguous Clang aggregate filler required')
            prefix=filler[1:]
        need(len(prefix) <= local['extent'], 'source aggregate initializer exceeds object extent')
        dtype=local['dtype'];typ=self.abi['canonical_types'][TYPE_KEYS[dtype]]
        lines=[]
        for index in range(local['extent']):
            if index < len(prefix):
                value=self.expression(prefix[index])
                need(value['category'] == 'exact-scalar' and value['source_type'] == typ, 'actual aggregate element conversion required')
                expression=value['expression']
            else: expression='(('+self._ctype(typ)+')0)'
            lines.append('dws_cpu_store_'+SUFFIX[dtype]+'('+self.thread+','+local['name']+','+str(index)+','+expression+');')
        return {'statements':lines,'source_declaration_sha256':digest(node),'source_initializer_sha256':digest(init),
            'source_order':'C++ aggregate elements left to right; trailing scalar value initialization',
            'ordinary_allocation_ownership_binding_required':True,'model_reset_called':False,'public_admission':False}
