from sly import Lexer, Parser


class RuleLexer(Lexer):
    """Given a string produce a series of Lex tokens"""

    tokens = {
        # tokens
        "RULE",
        "VARIABLE",
        "REGION",
        "NUMBER",
        # special symbols
        "AND",
        "OR",
        "EQUAL",
        "GREATER_THAN_EQUAL",
        "LESS_THAN_EQUAL",
        "CONDITIONAL_OPERATOR",
    }
    ignore = " \t"
    literals = {"+", "-", "*", "/", ">", "<", "!", ":", "(", ")"}

    # tokens
    REGION = r"region_oncoast"
    RULE = r"rule_([a-zA-z0-9]+)([^() ])*"
    VARIABLE = r"([a-zA-z]+)([^() ])*"
    NUMBER = r"-?\d+(\.\d+)?"

    # special symbols
    AND = r"&&"
    OR = r"\|\|"
    EQUAL = r"=="
    GREATER_THAN_EQUAL = r">="
    LESS_THAN_EQUAL = r"<="
    CONDITIONAL_OPERATOR = r"\?"


class RuleParser(Parser):
    """Parse through a series of Lex tokens and produce a parse tree"""

    tokens = RuleLexer.tokens

    precedence = (
        ("left", "CONDITIONAL_OPERATOR", ":"),
        ("left", "AND", "OR"),
        ("right", "!"),
        ("left", ">", "<", "GREATER_THAN_EQUAL", "LESS_THAN_EQUAL"),
        ("left", "+", "-"),
        ("left", "*", "/"),
    )

    def __init__(self):
        self.vars = {}
        self.region_var = None

    @_("expr")
    def statement(self, p):
        return p.expr

    # literals
    @_(
        'expr "+" expr',
        'expr "-" expr',
        'expr "*" expr',
        'expr "/" expr',
        'expr ">" expr',
        'expr "<" expr',
        "expr AND expr",
        "expr OR expr",
        "expr EQUAL expr",
        "expr LESS_THAN_EQUAL expr",
        "expr GREATER_THAN_EQUAL expr",
    )
    def expr(self, p):
        return (p[1], p.expr0, p.expr1)

    @_('"(" expr ")"')
    def expr(self, p):
        return p.expr

    @_('"!" expr')
    def expr(self, p):
        return (p[0], p.expr)

    @_('expr CONDITIONAL_OPERATOR expr ":" expr')
    def expr(self, p):
        return (p[1], p.expr0, p.expr1, p.expr2)

    @_("NUMBER")
    def expr(self, p):
        return float(p.NUMBER)

    @_("REGION")
    def expr(self, p):
        self.region_var = p.REGION
        return p.REGION

    @_("RULE")
    def expr(self, p):
        return p.RULE

    @_("VARIABLE")
    def expr(self, p):
        variable, time_of_year, temporal, spatial, percentile = p.VARIABLE.split("_")
        variables = {
            p.VARIABLE: {
                "variable": variable,
                "time_of_year": time_of_year,
                "temporal": temporal,
                "spatial": spatial,
                "percentile": percentile,
            }
        }
        if p.VARIABLE not in self.vars.keys():
            self.vars.update(variables)
        return p.VARIABLE

    def error(self, p):
        raise SyntaxError("Invalid Syntax {}".format(p))


def build_parse_tree(rule):
    """Given a rule expression break down the components into a parse tree"""
    lexer = RuleLexer()
    parser = RuleParser()

    # return parse tree AND all the variables used in the parse tree
    return parser.parse(lexer.tokenize(rule)), parser.vars, parser.region_var
