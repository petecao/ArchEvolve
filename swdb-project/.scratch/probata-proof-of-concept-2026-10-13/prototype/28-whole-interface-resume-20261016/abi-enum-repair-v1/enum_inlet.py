# 2026-10-16 ET. Closed two-stream enum inlet; inserted into a versioned copy.
ENUM_STREAMS = {
    (67258, 'ccd67cad5d4ff1fcd808c9a3835a18ba1bd07f099f6c0a98a15f7b8e31ffc13c'):
        ('first-source-v10', '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/control/compiler_abi_probe_v1.cpp'),
    (67405, 'd77d65757f0b41c601973d36972c2fa7d2a80b49296d3df13da5fcd99425bdbf'):
        ('memory-source-g642', '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-memory-tu-2baf722f-v1/control/compiler_abi_probe_v1.cpp'),
}
ENUM_EXPRESSIONS = {
    'char_bit': ('CHAR_BIT', 'int', 'IntegerLiteral'),
    'int_bits': ('sizeof(int) * CHAR_BIT', '__size_t', 'BinaryOperator'),
    'pointer_bits': ('sizeof(void *) * CHAR_BIT', '__size_t', 'BinaryOperator'),
    'little_endian': ('__BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__', 'bool', 'BinaryOperator'),
    **{'size_' + key: ('sizeof(dws_probe_' + key + ')', '__size_t', 'UnaryExprOrTypeTraitExpr') for key in TYPE_KEYS},
    **{'align_' + key: ('alignof(dws_probe_' + key + ')', '__size_t', 'UnaryExprOrTypeTraitExpr') for key in TYPE_KEYS},
    'float_radix': ('FLT_RADIX', 'int', 'IntegerLiteral'),
    'float_mantissa': ('FLT_MANT_DIG', 'int', 'IntegerLiteral'),
    'double_mantissa': ('DBL_MANT_DIG', 'int', 'IntegerLiteral'),
    'source_cores': ('NUM_CORES', 'int', 'IntegerLiteral'),
    'source_tiles': ('NUM_TILES', 'int', 'ParenExpr'),
    'source_registers': ('NUM_SCALAR_REGS', 'int', 'ParenExpr'),
    'source_tile_words': ('TILE_SIZE', 'int', 'IntegerLiteral'),
}


def _enum_profile(raw, probe_path):
    """Only the two exact strict streams can enter the new interpretation."""
    if type(raw) is not bytes or len(raw) not in {row[0] for row in ENUM_STREAMS}: return None
    profile = ENUM_STREAMS.get((len(raw), sha(raw)))
    if profile is not None:
        need(str(Path(probe_path).resolve()) == profile[1], 'exact original enum probe coordinate required')
    return profile


def _enum_point(point, probe_path):
    need(type(point) is dict, 'direct probe source point required')
    if 'expansionLoc' in point:
        need(set(point) == {'spellingLoc', 'expansionLoc'}, 'closed macro source location required')
        point = point['expansionLoc']
    need(type(point) is dict and {'offset', 'col', 'tokLen'} <= set(point)
        and set(point) <= {'offset', 'col', 'tokLen', 'file', 'line', '_file', '_line'}
        and all(type(point[field]) is int and point[field] >= 0 for field in ('offset', 'col', 'tokLen'))
        and point['tokLen'] > 0 and ('file' not in point or point['file'] == probe_path),
        'bounded original probe source point required')
    return point['offset'], point['tokLen']


def _enum_span(node, probe_path, probe_bytes):
    span = node.get('range')
    need(type(span) is dict and set(span) == {'begin', 'end'}, 'closed enum source range required')
    start, _ = _enum_point(span['begin'], probe_path)
    end, length = _enum_point(span['end'], probe_path)
    need(0 <= start <= end < end + length <= len(probe_bytes), 'enum source range outside pinned probe')
    return start, end + length


def _enum_source_value(root, key, probe_path, probe_bytes):
    """Select the initializer's own APValue, never an operand's literal.

    Exact Clang 22.1.8 SemaDecl.cpp inserts the integral conversion outside the
    original ConstantExpr. In this closed nonnegative uint32 domain that cast is
    value preserving. APValue.cpp prints a bool APValue as true/false; only the
    exact endian comparison below admits that spelling. This is a parser premise
    for two pinned observations, not a compiler or original-source theorem.
    """
    need(type(probe_bytes) is bytes and len(probe_bytes) == 1588 and sha(probe_bytes) == ABI_PROBE_SHA
        and key in ENUM_EXPRESSIONS, 'exact original enum probe bytes/key required')
    expression, typename, expression_kind = ENUM_EXPRESSIONS[key]
    expected_type = ({'qualType': '__size_t', 'desugaredQualType': 'unsigned long'} if typename == '__size_t'
                     else {'qualType': typename})
    need(type(root) is dict and set(root) == {'id', 'kind', 'loc', 'range', 'name', 'type', 'inner'}
        and root['kind'] == 'EnumConstantDecl' and root['name'] == 'dws_probe_' + key
        and root['type'] == {'qualType': '(unnamed enum at ' + probe_path + ':12:1)'}
        and type(root['inner']) is list and len(root['inner']) == 1, 'exact original enum declaration shape required')
    name_at, name_len = _enum_point(root['loc'], probe_path)
    need(probe_bytes[name_at:name_at + name_len] == root['name'].encode('ascii'), 'enum declaration name/source differs')
    cast = root['inner'][0]
    need(type(cast) is dict and set(cast) == {'id', 'kind', 'range', 'type', 'valueCategory', 'castKind', 'inner'}
        and cast['kind'] == 'ImplicitCastExpr' and cast['type'] == {'qualType': 'unsigned int'}
        and cast['valueCategory'] == 'prvalue' and cast['castKind'] == 'IntegralCast'
        and type(cast['inner']) is list and len(cast['inner']) == 1, 'single enum uint32 IntegralCast required')
    constant = cast['inner'][0]
    need(type(constant) is dict and set(constant) == {'id', 'kind', 'range', 'type', 'valueCategory', 'value', 'inner'}
        and constant['kind'] == 'ConstantExpr' and constant['type'] == expected_type
        and constant['valueCategory'] == 'prvalue' and type(constant['value']) is str
        and type(constant['inner']) is list and len(constant['inner']) == 1
        and type(constant['inner'][0]) is dict and constant['inner'][0].get('kind') == expression_kind
        and constant['inner'][0].get('type') == expected_type, 'one exact typed initializer ConstantExpr required')
    start, end = _enum_span(constant, probe_path, probe_bytes)
    need((start, end) == _enum_span(cast, probe_path, probe_bytes)
        and probe_bytes[start:end].decode('ascii') == expression
        and (name_at, end) == _enum_span(root, probe_path, probe_bytes), 'exact source enum initializer span required')
    # Check the entire fixed expression subtree. A second ConstantExpr, effect,
    # call, declaration reference or other expression is never hidden by search.
    stack = [constant['inner'][0]]
    while stack:
        node = stack.pop()
        need(type(node) is dict and node.get('kind') in {'IntegerLiteral', 'BinaryOperator',
            'UnaryExprOrTypeTraitExpr', 'ImplicitCastExpr', 'ParenExpr'}, 'unadmitted enum initializer expression')
        children = node.get('inner', [])
        need(type(children) is list, 'enum initializer children must be a list')
        stack.extend(children)
    value = constant['value']
    if key == 'little_endian':
        need(typename == 'bool' and value in {'true', 'false'}
            and constant['inner'][0].get('opcode') == '==', 'exact endian bool APValue required')
        return 1 if value == 'true' else 0
    need(typename != 'bool' and re.fullmatch('[0-9]+', value) and len(value) <= 10,
         'nonnegative integral own APValue required')
    result = int(value)
    need(result <= 4294967295, 'enum conversion must preserve the observed uint32 value')
    return result
