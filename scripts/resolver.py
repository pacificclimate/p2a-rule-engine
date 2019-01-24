from sly import Lexer, Parser
from decimal import Decimal


class RuleLexer(Lexer):
    tokens = {
        # tokens
        'RULE',
        'VARIABLE',
        'NUMBER',

        # special symbols
        'AND',
        'OR',
        'EQUAL',
        'GREATER_THAN_EQUAL',
        'LESS_THAN_EQUAL',
        'TERNARY'
    }
    ignore = ' \t'
    literals = {'+', '-', '*', '/', '>', '<', '!', ':', '(', ')'}

    # tokens
    RULE = r'rule_([a-zA-z0-9]+)([^() ])*'
    VARIABLE = r'([a-zA-z]+)([^() ])*'
    NUMBER = r'-?\d+(\.\d+)?'

    # special symbols
    AND = r'&&'
    OR = r'\|\|'
    EQUAL = r'=='
    GREATER_THAN_EQUAL = r'>='
    LESS_THAN_EQUAL = r'<='
    TERNARY = r'\?'


class RuleParser(Parser):
    tokens = RuleLexer.tokens

    # still unsure about how 'correct' this section is
    precedence = (
        ('left', 'TERNARY', ':'),
        ('left', 'AND', 'OR'),
        ('left', '>', '<'),
        ('left', 'GREATER_THAN_EQUAL', 'LESS_THAN_EQUAL'),
        ('left', '+', '-'),
        ('left', '*', '/'),
        ('right', '!')
    )

    def __init__(self):
        self.vars = set()

    @_('expr')
    def statement(self, p):
        return p.expr

    # literals
    @_('expr "+" expr',
       'expr "-" expr',
       'expr "*" expr',
       'expr "/" expr',
       'expr ">" expr',
       'expr "<" expr')
    def expr(self, p):
        return (p[1], p.expr0, p.expr1)

    @_('"(" expr ")"')
    def expr(self, p):
        return p.expr

    @_('"!" expr')
    def expr(self, p):
        return (p[0], p.expr)

    @_('expr AND expr',
       'expr OR expr',
       'expr EQUAL expr',
       'expr LESS_THAN_EQUAL expr',
       'expr GREATER_THAN_EQUAL expr',
       )
    def expr(self, p):
        return (p[1], p.expr0, p.expr1)

    @_('expr TERNARY expr ":" expr')
    def expr(self, p):
        return (p[1], p.expr0, p.expr1, p.expr2)

    @_('NUMBER')
    def expr(self, p):
        return Decimal(p.NUMBER)

    @_('RULE')
    def expr(self, p):
        return p.RULE

    @_('VARIABLE')
    def expr(self, p):
        self.vars.add(p.VARIABLE)
        return p.VARIABLE

    def error(self, p):
        raise SyntaxError('Invalid Syntax {}'.format(p))


def build_parse_tree(data):
    lexer = RuleLexer()
    parser = RuleParser()

    # return parse tree AND all the variables used in the parse tree
    return parser.parse(lexer.tokenize(data)), parser.vars
