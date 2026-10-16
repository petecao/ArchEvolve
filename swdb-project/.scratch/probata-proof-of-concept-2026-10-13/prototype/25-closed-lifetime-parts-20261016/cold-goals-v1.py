"""Independent 23-leaf transcription and exact reference reconstruction.

This is inert source metadata. No old target, sibling conclusion or proof is a
premise. The complete ten-conjunct positive source premise is repeated per leaf.
"""

PARTS_PREMISE_ACSL = (
    'Heap::well_formed(before) && 0 < n <= 2147483647 && t25_private_frame(entry,before) && '
    '!Heap::live(entry,r) && Heap::typed_writes(before,r,0,24,8) && '
    '!Heap::freeable(before,r,0) && b == Heap::fresh_id(before) && '
    't25_frame(before,loop,r,0) && t25v3_ctor_inv(loop,r,0,b,n,n,7)')
PARTS_QUANTIFIERS = r'\forall Heap::heap entry,before,loop; \forall integer r,b,n; '
PARTS_BASE_BINDINGS = '(entry heap) (before heap) (loop heap) (r Int) (b Int) (n Int)'
PARTS_POSITIVE_ACSL = 't25_closed_positive(loop,r,n)'
PARTS_FINAL_ACSL = 'Heap::end_automatic(Heap::release('+PARTS_POSITIVE_ACSL+',b),r)'
PARTS_FINAL = '(end_automatic (release '+POSITIVE_STATE+' b) r)'
PARTS_SCALAR_ACSL = '(n > 0 ? Heap::load_int('+PARTS_POSITIVE_ACSL+',b,0) : 0)'


def leaf_rows():
    """Id, fresh indices, local scope and conclusion in independent SMT/ACSL."""
    rows = []
    def add(ident, bind, scope, conclusion, acsl_bind, acsl_scope, acsl_conclusion):
        rows.append({'id':ident, 'bindings':bind, 'scope':scope, 'conclusion':conclusion,
                     'ACSL_bindings':acsl_bind, 'ACSL_scope':acsl_scope,
                     'ACSL_conclusion':acsl_conclusion})
    def observer(prefix, left, right, acsl_left, acsl_right):
        add(prefix+'.objects', '(object Int)', '(live entry object)',
            '(same_object '+left+' '+right+' object)',
            r'\forall integer object; ', 'Heap::live(entry,object)',
            'Heap::same_object('+acsl_left+','+acsl_right+',object)')
        for suffix, operation, relation in [('contents','contents','=='),
                                            ('initialization','initialized_at','<==>')]:
            conclusion='(= ('+operation+' '+left+' observed position) ('+operation+' '+right+' observed position))'
            acsl='Heap::'+operation+'('+acsl_left+',observed,position) '+relation+' Heap::'+operation+'('+acsl_right+',observed,position)'
            if relation=='<==>':acsl='('+acsl+')'
            add(prefix+'.'+suffix, '(observed Int) (position Int)', '(live entry observed)',
                conclusion, r'\forall integer observed,position; ', 'Heap::live(entry,observed)', acsl)
    observer('positive.exit_image.frame','entry',POSITIVE_STATE,'entry',PARTS_POSITIVE_ACSL)
    for ident, conclusion, acsl in [
        ('private.receiver','(not (live entry r))','!Heap::live(entry,r)'),
        ('private.buffer','(or (= b 0) (and (not (live entry b)) (not (= b r))))',
         '(b == 0 || (!Heap::live(entry,b) && b != r))'),
        ('receiver_access','(typed_writes '+POSITIVE_STATE+' r 0 24 8)',
         'Heap::typed_writes('+PARTS_POSITIVE_ACSL+',r,0,24,8)'),
        ('receiver_nonfreeable','(not (freeable '+POSITIVE_STATE+' r 0))',
         '!Heap::freeable('+PARTS_POSITIVE_ACSL+',r,0)'),
        ('buffer_freeable','(freeable '+POSITIVE_STATE+' b 0)',
         'Heap::freeable('+PARTS_POSITIVE_ACSL+',b,0)'),
    ]:add('positive.exit_image.'+ident,'','',conclusion,'','',acsl)
    offset='(+ 0 (* 4 j))'
    location=POSITIVE_STATE+' b '+offset
    acsl_location=PARTS_POSITIVE_ACSL+',b,(0+4*j)'
    load='(load_int '+location+')'
    acsl_load='Heap::load_int('+acsl_location+')'
    for ident, conclusion, acsl in [
        ('access','(typed_reads '+location+' 4 4)','Heap::typed_reads('+acsl_location+',4,4)'),
        ('initialization','(initialized_at '+location+')','Heap::initialized_at('+acsl_location+')'),
        ('integer','(integer_at '+location+' '+load+')','Heap::integer_at('+acsl_location+','+acsl_load+')'),
        ('bounds','(and (<= (- 2147483648) '+load+') (<= '+load+' 2147483647))',
         '-2147483648 <= '+acsl_load+' <= 2147483647'),
    ]:add('positive.exit_image.integer.'+ident,'(j Int)','(and (<= 0 j) (< j n))',conclusion,
          r'\forall integer j; ','0 <= j < n',acsl)
    for ident, conclusion, acsl in [
        ('initialization','(initialized_at '+POSITIVE_STATE+' b (* 4 j))',
         'Heap::initialized_at('+PARTS_POSITIVE_ACSL+',b,4*j)'),
        ('value','(integer_at '+POSITIVE_STATE+' b (* 4 j) 7)',
         'Heap::integer_at('+PARTS_POSITIVE_ACSL+',b,4*j,7)'),
    ]:add('positive.exit_image.filled.'+ident,'(j Int)','(and (<= 0 j) (< j n))',conclusion,
          r'\forall integer j; ','0 <= j < n',acsl)
    add('positive.cleanup.scalar','','',
        '(= (ite (< 0 n) (load_int '+POSITIVE_STATE+' b 0) 0) (ite (< 0 n) 7 0))',
        '','',PARTS_SCALAR_ACSL+' == (n > 0 ? 7 : 0)')
    observer('positive.cleanup.frame','entry',PARTS_FINAL,'entry',PARTS_FINAL_ACSL)
    observer('positive.cleanup.observes',POSITIVE_STATE,PARTS_FINAL,PARTS_POSITIVE_ACSL,PARTS_FINAL_ACSL)
    for ident, target in [('receiver_dead','r'),('buffer_dead','b')]:
        add('positive.cleanup.'+ident,'','','(not (forms '+PARTS_FINAL+' '+target+' 0))',
            '','','!Heap::forms('+PARTS_FINAL_ACSL+','+target+',0)')
    require(len(rows)==23 and len({r['id'] for r in rows})==23,'independent exact23 distinct source leaves')
    return rows


def source_goal(ident, *, positive_branch=False):
    row=next(r for r in leaf_rows() if r['id']==ident)
    premise=forms(POSITIVE_PREMISE)[0]
    if row['scope']:premise=['and',*premise[1:],forms(row['scope'])[0]]
    conclusion=row['conclusion']
    if positive_branch and ident=='positive.cleanup.scalar':
        conclusion='(= (load_int '+POSITIVE_STATE+' b 0) 7)'
    bindings=forms('('+PARTS_BASE_BINDINGS+' '+row['bindings']+')')[0]
    return ['not',['forall',bindings,['=>',premise,forms(conclusion)[0]]]]


def source_statement(row):
    return PARTS_QUANTIFIERS+row['ACSL_bindings']+PARTS_PREMISE_ACSL+(
        ' && '+row['ACSL_scope'] if row['ACSL_scope'] else '')+' ==> '+row['ACSL_conclusion']


def reference_statement(name):
    positive=PARTS_POSITIVE_ACSL; final=PARTS_FINAL_ACSL; scalar=PARTS_SCALAR_ACSL
    if name=='positive.exit_image':
        body=('t25_private_frame(entry,'+positive+') && t25_private_ids(entry,r,b) && '
              'Heap::typed_writes('+positive+',r,0,24,8) && !Heap::freeable('+positive+',r,0) && '
              'Heap::freeable('+positive+',b,0) && Heap::int32_region('+positive+',b,0,n) && '
              'Heap::filled_prefix('+positive+',b,n,7)')
    elif name=='positive.cleanup':
        body=(r'\exists Heap::heap final; \exists integer scalar; final == '+final+' && scalar == '+scalar+
              ' && scalar == (n > 0 ? 7 : 0) && t25_private_frame(entry,final) && '
              't25_private_observes(entry,'+positive+',final) && !Heap::forms(final,r,0) && !Heap::forms(final,b,0)')
    else:raise ValueError('unknown independent original reference')
    return PARTS_QUANTIFIERS+PARTS_PREMISE_ACSL+' ==> '+body


def source_zero_addition(value):
    """Exact mathematical integer additive identity; no comparison weakening."""
    if isinstance(value,str):return value
    value=[source_zero_addition(x) for x in value]
    if value and value[0]=='+':
        rest=[x for x in value[1:] if x!='0']
        return '0' if not rest else rest[0] if len(rest)==1 else ['+',*rest]
    return value


def goal_variants(ident):
    variants=[('literal_source',source_goal(ident))]
    if ident=='positive.cleanup.scalar':
        variants.append(('retained_positive_premise_scalar_branch',source_goal(ident,positive_branch=True)))
    variants += [(name+'_definition_and_fresh_buffer_substitution',positive_source_reduction(ident,value))
                 for name,value in list(variants)]
    variants += [(name+'_zero_additive_identity',source_zero_addition(value)) for name,value in list(variants)]
    # Exact variants are retained; duplicate normal forms are harmless metadata.
    return variants


def source_reference_equivalence(manifest):
    """Check all leaf source syntax and reconstruct both original references.

    The only composition rules are conjunction, fresh universal distribution,
    checked source definitions, and explicit existential equality witnesses.
    This reconstructs formulas; it never treats a leaf or reference as proved.
    """
    rows=leaf_rows();require([r['id'] for r in rows]==[r['id'] for r in manifest['obligations']],
                            'exact full23 source target order')
    require(manifest['complete_positive_antecedent']==PARTS_PREMISE_ACSL,'exact full source premise')
    output=[]
    for row,actual in zip(rows,manifest['obligations'],strict=True):
        require(actual['statement']==source_statement(row) and actual['source_antecedent']==PARTS_PREMISE_ACSL and
                actual['derived_index_scope']==row['ACSL_scope'] and not actual['dependencies'],
                'independent full source formula/scoped-index binding '+row['id'])
        require(not (set(re.findall(r'\b\w+\b',PARTS_PREMISE_ACSL)) &
                     {x[0] for x in forms('('+row['bindings']+')')[0]}),'fresh scoped source indices '+row['id'])
        output.append({'id':row['id'],'full_source_statement_sha256':hashlib.sha256(source_statement(row).encode()).hexdigest(),
                       'independent_source_goal_sha256':digest(source_goal(row['id'])),
                       'scoped_indices_fresh':True,'caller_or_sibling_premises_added':False})
    for name in ('positive.exit_image','positive.cleanup'):
        group=manifest['conjunctions'][name]
        wanted=[r['id'] for r in rows if r['id'].startswith(name+'.')]
        require(group['parts']==wanted and not group['premises_added'] and not group['dependencies'] and
                group['antecedent']==PARTS_PREMISE_ACSL,'complete exact same-premise reference components '+name)
        require(group['original_statement']==reference_statement(name),'independent exact original reference statement '+name)
    cleanup=manifest['conjunctions']['positive.cleanup']
    require(cleanup['witnesses']=={'final':PARTS_FINAL_ACSL,'scalar':PARTS_SCALAR_ACSL} and
            cleanup['reflexive_equalities']==[PARTS_FINAL_ACSL+' == '+PARTS_FINAL_ACSL,
                                               PARTS_SCALAR_ACSL+' == '+PARTS_SCALAR_ACSL],
            'exact final/scalar existential witnesses and reflexive equalities')
    return {'leaves':output,'original_references_proved':False,
            'exit_components':14,'cleanup_components':9,
            'full_premise_each_leaf':True,'fresh_universal_scopes_checked':True,
            'explicit_final_and_scalar_witnesses_checked':True,
            'composition':'Complete conjunction distribution and capture-free source-definition expansion with fixed existential equality witnesses; no proof result inferred.'}
