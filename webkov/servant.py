from collections import deque, defaultdict, Counter, namedtuple
from random import choice
import termcolor

from webkov.helper import filtered_model

from webkov.parser import name_dialog_deques, TRAILING_PUNCT_SET
from webkov.parser import SENTENCE_ENDINGS


# first:
# woohoo! pretty looking shakespeare!
def prose(start=(".",), name='JULIET', num_tokens=75):
    print(pretty(
        generate_tokens(start=start, name=name, num_tokens=num_tokens)))


# if any of these characters are commented out, it's because
# throughout the entire play they do not end a sentence.

CHARACTERS = {
    'MERCUTIO',
    # 'SECOND WATCHMAN',
    'NURSE',
    'PARIS',
    'GREGORY',
    # 'PETER',
    # 'THIRD MUSICIAN',          
    # 'ABRAHAM',
    # 'SECOND MUSICIAN',
    'SECOND SERVANT',
    'BENVOLIO',
    'SECOND CAPULET',
    'FIRST SERVANT',
    'SAMPSON',
    'BALTHASAR',
    'SERVANT',
    # 'FIRST CITIZEN',
    'LADY CAPULET',
    'ROMEO',
    # 'FIRST MUSICIAN',
    'MONTAGUE',
    'FIRST WATCHMAN',
    'COMMON',
    'LADY MONTAGUE',
    'PRINCE',
    'CHORUS',
    # 'THIRD WATCHMAN',
    'CAPULET',
    'FRIAR JOHN',
    # 'MUSICIAN',
    'PAGE',
    'FRIAR LAURENCE',
    'TYBALT',
    'NURSE',
    'APOTHECARY',
    'LADY CAPULET',
    'JULIET'
}

def uppercase_first_tok(tokens):
    ''' Takes tokens and uppercases the first letter '''

    out = tokens.copy()
    front = out.popleft()
    if type(front) == Colored_Token:
        # initialize a new one. thank lord these are immutable because
        # right now this codebase is a tire fire, and I wasn't sure
        # of the effects of copying all these deques.
        front = Colored_Token(
            front.token.capitalize(),
            front.order)
    else:
        front = front.capitalize()
    out.appendleft(front)
    return out


# hmm.. how am I going to map this to html?
# am I going to even care?
ORDER_COLOR_MAP = {
    0: 'white',
    1: 'cyan',
    2: 'green',
    3: 'yellow',
    4: 'red',
    5: 'magenta',
    # 1: 'magenta',
    # 2: 'red',
    # 3: 'yellow',
    # 4: 'green',
    # 5: 'cyan',
}


# TODO, splice it into pretty
def colored_transform(maybe_token, order_color_map=ORDER_COLOR_MAP):
    '''
    Take a token, and if it's just a string, return it as is.
    If it's tagged, return the colored version of it using termcolor
    '''
    if isinstance(maybe_token, Colored_Token):
        return termcolor.colored(maybe_token.token,
                                 order_color_map[maybe_token.order])
    else:
        return maybe_token


def pretty(tokens, line_min_chars=35, shakespeare=True,
           min_lines_before_break=(2, 8),
           sentence_endings=SENTENCE_ENDINGS,
           trailing_punct_set=TRAILING_PUNCT_SET):
    '''
    Super messy function.

    Returns a string of lines obtained from concatenating tokens until
    length is above line_min_chars. There is no guarantee returned
    strings don't exceed line_min_chars by an insane amount.  If we
    run out of tokens, join whatever, even if it's under
    line_min_chars. If when adding a line, we notice the length
    of our output is greater than min_lines_before_break, append a newline.

    Yeah, this function doesn't do what you want. ☠
    I'm assuming ascii here.
    '''
    prettified_lines = deque()

    lines_before_break = 0
    charcount = 0
    words = deque()

    toks = truncate(tokens.copy())
    while toks:
        # uses peekin!
        peek = toks[0] if type(toks[0]) == str else toks[0].token
        continue_line_predicate = (charcount < line_min_chars or
                                   peek in sentence_endings or
                                   peek in trailing_punct_set)
        if continue_line_predicate:
            tok = toks.popleft()
            if type(tok) == Colored_Token:
                charcount += len(tok.token)
            else:
                charcount += len(tok)
            words.append(tok)
        else:
            if lines_before_break > choice(range(*min_lines_before_break)):
                prettified_lines.append("")
                lines_before_break = 0
            # now we add another line
            lines_before_break += 1
            if words and shakespeare:
                words = uppercase_first_tok(words)
            line = "".join(map(colored_transform, padded(words)))
            prettified_lines.append(line)

            # reinitialize
            charcount = 0
            words = deque()
    if words:
        # don't worry about breaking anymore, this is the last one.
        if shakespeare:
            words = uppercase_first_tok(words)
        line = "".join(map(colored_transform, padded(words)))
        prettified_lines.append(line)
    return "\n".join(prettified_lines)


def padded(tokens):
    '''
    for each token, prepend a space to them provided they aren't punctuation
    Special case the first token.
    '''
    tokens = tokens.copy()
    out = deque([tokens.popleft()])
    while tokens:
        token = tokens.popleft()
        # we break the conditional up here so that we special case colored tokens
        # alternatively we could pass colored to padded.
        if type(token) == Colored_Token:
            if token.token not in TRAILING_PUNCT_SET:
                out.append(" ")
        elif token not in TRAILING_PUNCT_SET:
            out.append(" ")
        out.append(token)
    return out


def truncate(tokens, sentence_endings=SENTENCE_ENDINGS):
    '''
    Truncate on a complete sentence, identified by sentence_endings
    '''
    # iterate backwards
    while tokens:
        tok = tokens.pop()
        if type(tok) == Colored_Token:
            maybe_punct = tok.token
        else:
            maybe_punct = tok
        if maybe_punct in sentence_endings:
            tokens.append(maybe_punct)
            break
    return tokens


# TIL you need the trailing comma to for (".") to be a tuple.
def generate_tokens(start=(".",), order=1, num_tokens=75, name='COMMON'):
    " Return a deque. "

    # eh since we're top levelish, we might as well start doing assertions
    assert start
    # wrap the string in a tuple so we don't have to do it for order 1 chains.
    if isinstance(start, str):
        start = tuple(start)
    assert isinstance(start, tuple)

    words = name_dialog_deques()[name]
    chains = chain_from_deq(words, order=order)

    prefix = len(start)
    if order > prefix:
        # choose a random element starting with our start.
        start = choice([key for key in chains.keys()
                        if key[:prefix] == start])
    else:
        assert order == prefix

    if start not in chains:
        # rather than fall apart, just choose something
        print("{} does not have a {} in their model".format(name, start))
        start = choice(list(chains.keys()))
        # raise KeyError("{} is not in the dialog of {}".format(
        #     repr(start),
        #     name))

    out = deque()
    # special case the start token if it starts with a "."
    if start[0] in [".", "!", "?"]:
        out.extend(start[1:])
    else:
        out.extend(start)

    # to facilitate quick appends and left sided pops,
    # we'll just use a deque here.
    deq = deque(start)

    for _ in range(num_tokens):
        # if we wanted to choose between determinism, we'd do
        # it here.
        after = choice(list(
            chains[tuple(deq)].elements()))
        out.append(after)

        deq.popleft()  # drop off the stale element
        deq.append(after)  # use the new one

    return out


# one function > two
# maybe rewrite this in the context of a generator?
def chain_from_deq(deq, order=1, strict=True):
    deq = deq.copy()

    out = defaultdict(Counter)
    assert len(deq) > order
    keys = []
    # initialize keys
    for _ in range(order):
        keys.append(deq.popleft())
    # consume the tokens!
    while deq:
        after = deq.popleft()
        out[tuple(keys)][after] += 1
        # splice out the first key.
        keys = keys[1:]
        # and append what we just got
        keys.append(after)
    # after the deq has been consumed, if strict
    # filter out all the keys that aren't in the biggest
    # scc. Only order 1 is implemented so do nothing
    # if it fails
    if strict:
        try:
            out = filtered_model(out, order)
        except ValueError:
            pass
    return out


def gen_models(order=5, name='COMMON', _cache={}):
    out = {}
    if (order, name) in _cache:
        for i in range(1, order + 1):
            out[i] = _cache[i, name].copy()
        return out
    else:
        stream = name_dialog_deques()[name]
        for i in range(1, order + 1):
            if (i, name) not in _cache:
                _cache[(i, name)] = chain_from_deq(stream, order=i)
            out[i] = _cache[i, name].copy()
        return out




# can you use namedtuples for lightweight classes?
Colored_Token = namedtuple("Colored_Token", ['token', 'order'])


def legible(start=(".",), name='COMMON', num_tokens=75,
            max_order=5, tag=False):
    out = deque()
    stream = generate_legible(gen_models(order=max_order),
                              start, name, tag)
    for _ in range(num_tokens):
        out.append(next(stream))
    return out


def generate_legible(models, start=(".",), name='COMMON', tag=False):
    # an generator instead? this way we don't have to keep track of state.
    # assume start is a tuple
    order = len(start)
    assert start in models[order]
    max_order = len(models)
    curr = deque(start)
    while True:
        staging = curr.copy()
        descending_orders = reversed(range(1,
                                           min(len(staging), max_order) + 1))
        for curr_order in descending_orders:
            assert len(staging) <= max_order
            tup = tuple(staging)
            model = models[curr_order]
            # fall back to order 1 if nothing else.
            if tup in model and (not _is_determined(tup, model) or
                                 curr_order == 1):
                # we've found a valid candidate, or we were forced into it
                got = choice(list(
                    model[tup].elements()))

                curr.append(got)
                while len(curr) >= max_order:
                    curr.popleft()
                if tag:
                    yield Colored_Token(got, curr_order)
                else:
                    yield got
                break
            else:
                staging.popleft()



def _is_determined(token, model):
    ''' This maximizes the order while introducing an element of chance '''
    return len(model[token].keys()) <= 1

