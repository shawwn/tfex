import re
import sys
import importlib
import inspect

def module_from_fqn(fqn):
  fqn = re.sub("^np[.]", "numpy.", fqn)
  fqn = re.sub("^tf[.]", "tensorflow.", fqn)
  if fqn == 'np':
    fqn = 'numpy'
  if fqn == 'tf':
    fqn = 'tensorflow'
  # list alternatives for (module_name, local_fqn)
  parts = fqn.split(".")
  name_pairs = [(".".join(parts[:i]), ".".join(parts[i:])) for i in range(len(parts), 0, -1)]
  # try each alternative in turn
  for module_name, local_fqn in name_pairs:
    try:
      module = importlib.import_module(module_name) # may raise ImportError
      get(module, local_fqn) # may raise AttributeError
      return module, local_fqn
    except:
      pass
  # maybe some of the modules themselves contain errors?
  for module_name, _local_fqn in name_pairs:
    try:
      importlib.import_module(module_name) # may raise ImportError
    except ImportError:
      if not str(sys.exc_info()[1]).startswith("No module named '" + module_name + "'"):
        raise
  # maybe the requested attribute is missing?
  for module_name, local_fqn in name_pairs:
    try:
      module = importlib.import_module(module_name) # may raise ImportError
      get(module, local_fqn) # may raise AttributeError
    except ImportError:
      pass
  # we are out of luck, but we have no idea why
  raise ImportError(fqn)

def is_str(x):
  return isinstance(x, str) or isinstance(x, bytes)

def is_iterable(x):
  try:
    if is_str(x):
      return False
    xit = iter(x)
    return True
  except TypeError:
    return False

def listify(x):
  if is_iterable(x):
    return [_ for _ in x]
  return [x]

def as_iterable(x):
  return x if is_iterable(x) else [x]

def get(module, *args):
  if is_str(module):
    module, *args = module.split('.') + listify(args)
    module = lookup(module)
  if is_iterable(module):
    module = get(*module)
  obj = module
  for fqn in args:
    for part in fqn.split("."):
      if len(part) > 0:
        obj = getattr(obj, part)
  return obj

SYMBOL_PLAINVAL = 4
SYMBOL_VARALIAS = 1
SYMBOL_LOCALIZED = 2
SYMBOL_FORWARDED = 3

USE_LSB_TAG = False

#enum Lisp_Type
#{
#/* Symbol.  XSYMBOL (object) points to a struct Lisp_Symbol.  */
Lisp_Symbol = 0,

#/* Miscellaneous.  XMISC (object) points to a union Lisp_Misc,
#   whose first member indicates the subtype.  */
Lisp_Misc = 1,

#/* Integer.  XINT (obj) is the integer value.  */
Lisp_Int0 = 2,
Lisp_Int1 = 6 if USE_LSB_TAG else 3,

#/* String.  XSTRING (object) points to a struct Lisp_String.
#   The length of the string, and its contents, are stored therein.  */
Lisp_String = 4,

#/* Vector of Lisp objects, or something resembling it.
#   XVECTOR (object) points to a struct Lisp_Vector, which contains
#   the size and contents.  The size field also contains the type
#   information, if it's not a real vector object.  */
Lisp_Vectorlike = 5,

#/* Cons.  XCONS (object) points to a struct Lisp_Cons.  */
Lisp_Cons = 3 if USE_LSB_TAG else 6

Lisp_Float = 7
#}

class LispSymbol(object):
  def __init__(self, redirect=SYMBOL_PLAINVAL, alias=None, value=None):
    self.redirect = redirect
    self.alias = alias
    self.value = None

def make_lisp_symbol(self=None):
  if self is None:
    self = LispSymbol()
  self.redirect = SYMBOL_PLAINVAL
  self.alias = None
  self.value = None
  return self

def XSETSYMBOL(a, b):
  make_lisp_symbol(a)
  a.redirect = b.redirect
  a.alias = b.alias
  a.value = b.value
  return a

def eassume(x):
  assert x

def no(x):
  return x is None

def yes(x):
  return not no(x)

def SYMBOL_ALIAS(sym):
  eassume ((sym.redirect == SYMBOL_VARALIAS) and yes(sym.alias));
  return sym.alias;

Qnil = '|nil|'
Qunbound = '|unbound|'
Qvoid_variable = '|void-variable|'
Qcyclic_variable_indirection = '|cyclic-variable-indirection|'
Qwrong_type_argument = '|wrong-type-argument|'

class LispCons(object):
  def __init__(self):
    self.car = None
    self.cdr = None

def cons (car, cdr):
  val = LispCons()
  val.car = car
  val.cdr = cdr
  return val

def EQ (a, b):
  return a == b

def XSETCAR (c, n):
  assert(hasattr(c, 'car'))
  c.car = n

def XSETCDR (c, n):
  assert(hasattr(c, 'cdr'))
  c.cdr = n

Fcons = cons

def list1(arg1):
  return Fcons (arg1, Qnil)

def list2(arg1, arg2):
  return Fcons (arg1, Fcons (arg2, Qnil))

def list3(arg1, arg2, arg3):
  return Fcons (arg1, Fcons (arg2, Fcons (arg3, Qnil)))

def list4(arg1, arg2, arg3, arg4):
  return Fcons (arg1, Fcons (arg2, Fcons (arg3, Fcons (arg4, Qnil))))

def list5(arg1, arg2, arg3, arg4, arg5):
  return Fcons (arg1, Fcons (arg2, Fcons (arg3, Fcons (arg4, Fcons (arg5, Qnil)))))

def listn(x, *args):
  val = cons (x, Qnil)
  tail = val
  for arg in args:
    elem = cons (arg, Qnil)
    XSETCDR (tail, elem)
    tail = elem
  return val

def signal(error_symbol, data):
  raise Exception("uncaught signal {}: {}".format(error_symbol, data))

Fsignal = signal

def xsignal(error_symbol, data):
  Fsignal(error_symbol, data)

def xsignal0(error_symbol):
  xsignal (error_symbol, Qnil)

def xsignal1(error_symbol, arg):
  xsignal (error_symbol, list1(arg))

def indirect_variable(symbol):
  tortoise = hare = symbol
  while hare.redirect == SYMBOL_VARALIAS:
    hare = SYMBOL_ALIAS (hare);
    if hare.redirect != SYMBOL_VARALIAS:
      break;
    hare = SYMBOL_ALIAS (hare);
    tortoise = SYMBOL_ALIAS (tortoise);
    if hare == tortoise:
      tem = LispSymbol()
      tem = XSETSYMBOL (tem, symbol);
      xsignal (Qcyclic_variable_indirection, tem);
  return hare

def wrong_type_argument(predicate, value):
  xsignal (Qwrong_type_argument, predicate, value)

def CHECK_TYPE(ok, predicate, x):
  if not ok:
    wrong_type_argument(predicate, x)

def CHECK_SYMBOL (sym):
  assert(hasattr(sym, 'redirect'))

def XSYMBOL (sym):
  return sym

def SYMBOL_VAL (sym):
  assert(sym.redirect == SYMBOL_PLAINVAL)
  return sym.value

def SET_SYMBOL_VAL (sym, newval):
  assert(sym.redirect == SYMBOL_PLAINVAL)
  sym.value = newval

def find_symbol_value(symbol):
  sym = symbol
  while True:
    if sym.redirect == SYMBOL_VARALIAS:
      sym = indirect_variable (sym)
      continue
    elif sym.redirect == SYMBOL_PLAINVAL:
      return SYMBOL_VAL (sym)
    elif sym.redirect == SYMBOL_LOCALIZED:
      #struct Lisp_Buffer_Local_Value *blv = SYMBOL_BLV (sym);
      #swap_in_symval_forwarding (sym, blv);
      #return blv->fwd ? do_symval_forwarding (blv->fwd) : blv_value (blv);
      assert(False) # not yet implemented
      #/* FALLTHROUGH */
    if sym.redirect == SYMBOL_FORWARDED:
      return do_symval_forwarding (SYMBOL_FWD (sym));
    emacs_abort ()

def symbol_value (symbol):
  val = find_symbol_value (symbol)
  if not EQ(val, Qunbound):
    return val
  xsignal1 (Qvoid_variable, symbol)

def set_internal (symbol, newval, where, bindflag):
  CHECK_SYMBOL (symbol)
  sym = XSYMBOL (symbol);
  while True:
    if sym.redirect == SYMBOL_VARALIAS:
      sym = indirect_variable (sym)
      continue
    elif sym.redirect == SYMBOL_PLAINVAL:
      SET_SYMBOL_VAL (sym, newval)
      return
    elif sym.redirect == SYMBOL_LOCALIZED:
      emacs_abort() # TODO
    elif sym.redirect == SYMBOL_FORWARDED:
      emacs_abort() # TODO
    emacs_abort()

SET_INTERNAL_SET = 0
SET_INTERNAL_BIND = 1
SET_INTERNAL_UNBIND = 2
SET_INTERNAL_THREAD_SWITCH = 3

def set (symbol, newval):
  set_internal (symbol, newval, Qnil, SET_INTERNAL_SET)
  return newval

Fset = set

def SYMBOLP(x):
  return is_str(x) and len(x) > 1 and x[0] == '|' and x[-1] == '|'

def evaluate(form):
  pass

def lookup(fqn):
  module, fqn = module_from_fqn(fqn)
  return get(module, fqn)

def call(fqn, *args, **kwargs):
  f = get(fqn)
  assert callable(f)
  return f(*args, **kwargs)

def dirof(fqn):
  module, _ = module_from_fqn(fqn)
  return os.path.dirname(inspect.getfile(module))

def toplevel(obj):
  return callable(obj) and obj.__name__ in sys.modules[obj.__module__].__dict__

def intern(obj):
  if is_str(obj):
    return obj
  assert toplevel(obj)
  return obj.__module__ + "." + obj.__name__



