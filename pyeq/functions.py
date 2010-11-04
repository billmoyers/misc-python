import copy
import math

class Function:
	PREFIX = 0
	INFIX = 1
	
	cardinality = 0	
	commutative = False
	associative = False
	
	defaultSimplify = None
	
	def __init__(self, name, *children, **attr):
		self.name = name
		self.children = [self._wrap(c) for c in children]
		self.fix = Function.PREFIX
		
		if attr.has_key('infix') and attr['infix']:
			self.fix = Function.INFIX

	def _wrap(self, f):
		if not isinstance(f, Function):
			return Constant(float(f))
		else:
			return f
	
	def __repr__(self):
		if len(self.children) == 0:
			return self.name
			
		elif self.fix == Function.PREFIX:
			return '%s(%s)' % (self.name, ','.join([str(c) for c in self.children]))
		
		elif self.fix == Function.INFIX:
			return '(%s)' % self.name.join([str(c) for c in self.children])

	def __getitem__(self, i):
		return self.children[i]

	def __len__(self):
		return reduce(lambda x, y : x + len(y), self.children, 1)

	def __hash__(self):
		return hash(self.children)

	def __eq__(self, other):
		if not isinstance(other, Function):
			return False
			
		if len(other.children) != len(self.children):
			return False
		
		if self.name != other.name:
			return False
		
		return reduce(lambda x, y : x and y[0] == y[1], zip(self.children, other.children), True)
		
	def __contains__(self, needle):
		if self == needle:
			return True
			
		return reduce(lambda x, y : x or needle in y, self.children, False)

	def __add__(self, other):
		if isinstance(other, Function):
			return Add(self, other)
			
		else:
			return Add(self, Constant(str(other)))

	def __radd__(self, other):
		if isinstance(other, Function):
			return Add(other, self)
			
		else:
			return Add(Constant(str(other)), self)

	def __mul__(self, other):
		if isinstance(other, Function):
			return Mul(self, other)
			
		else:
			return Mul(self, Constant(str(other)))

	def __rmul__(self, other):
		if isinstance(other, Function):
			return Mul(other, self)
			
		else:
			return Mul(Constant(str(other)), self)

	def __pow__(self, other):
		if isinstance(other, Function):
			return Pow(self, other)
			
		else:
			return Pow(self, Constant(str(other)))

	def __rpow__(self, other):
		if isinstance(other, Function):
			return Pow(other, self)
			
		else:
			return Pow(Constant(str(other)), self)

	def __sub__(self, other):
		return self + Constant(-1) * other
		
	def __rsub__(self, other):
		return other + Constant(-1) * self

	def __div__(self, other):
		return self * (other ** Constant(-1))

	def __rdiv__(self, other):
		return other * (self ** Constant(-1))
		
	def simplify(self, **methods):
		#print 'simplify(%s)' % self
	
		if methods.has_key(self.__class__.__name__):
			return methods[self.__class__.__name__](self, **methods)
		elif self.__class__.defaultSimplify != None:
			return self.__class__.defaultSimplify(self, **methods)
		else:
			r = copy.copy(self)
			r.children = [c.simplify(**methods) for c in r.children]
			return r

	def evaluate(self, vals):
		for k, v in vals.items():
			if self == k:
				return v
		
		c = copy.copy(self)
		c.children = map(lambda x : x.evaluate(vals), self.children)
		return c
		
class Constant (Function):
	cardinality = 0
	def __init__(self, a):
		Function.__init__(self, str(a))
		
	def __repr__(self):
		return self.name
		
	def getValue(self):
		f = None
		i = None
		try:
			f = float(self.name)
			i = int(self.name)
		except:
			pass
			
		if i == None: return f
		else: return i

class Variable (Function):
	cardinality = 0
	def __init__(self, a):
		Function.__init__(self, str(a))

	def __repr__(self):
		return self.name

class Add (Function):
	cardinality = 2
	commutative = True
	associative = True
	
	defaultSimplify = lambda f, **methods : f._reduce(**methods)
	
	def __init__(self, a, b):
		Function.__init__(self, '+', a, b, infix = True)
		
	def _reduce(self, **methods):
		n = 0
		others = []
		
		for f in self.children:
			f = f.simplify(**methods)
			
			if isinstance(f, Constant):
				n += f.getValue()
			
			else:
				others.append(f)
		
		if n != 0: others.append(Constant(n))
		if len(others) == 0: return Constant(0)
		if len(others) == 1: return others[0]
		return Add(*others)
		
class Mul (Function):
	cardinality = 2
	commutative = True
	associative = True
	
	defaultSimplify = lambda f, **methods : f._flatten(**methods)._reduce(**methods)
	
	def __init__(self, a, b):
		Function.__init__(self, '*', a, b, infix = True)

	def _flatten(self, **methods):
		mults = self.children[:]
		rm = None
		
		while rm == None or len(rm) > 0:
			am = []
			rm = []
				
			for m in mults:
				if isinstance(m, Mul):
					am.extend(m.children)
					rm.append(m)
			
			mults = filter(lambda m : m not in rm, mults)
			mults.extend(am)
			
		r = copy.copy(self)
		r.children = mults
		return r

	def _reduce(self, **methods):
		#print 'Mul._reduce'
		dargs = []
		add = None
		mult = None
		num = 1
		
		# Reduce to addition, multiplication, and a constant
		
		for f in self.children:
			if f == Constant(0):
				return Constant(0)
			
			elif isinstance(f, Constant):
				num *= f.getValue()
				
			elif isinstance(f, Add):
				if add == None:
					add = f
					
				else:
					dist = None
					for a in f.children:
						for b in f.children:
							if dist == None:
								dist = a*b
							else:
								dist += (a*b)
								
					add = dist
			else:
				if mult == None:
					mult = f
				else:
					mult *= f
		
		#print '  %s %s %s' % (num, add, mult)
		
		if num == 1: num = None
		
		if mult == None and num != None: mult = num
		elif mult != None and num != None: mult *= num
		
		if add == None and mult == None: return Constant(1)
		elif add == None:
			if isinstance(mult, Function):
				r = copy.copy(mult)
				r.children = [c for c in [c.simplify(**methods) for c in r.children] if not isinstance(c, Constant) or c.getValue() != 1]
				if len(r.children) == 1:
					return r.children[0]
				else:
					return r
			else:
				return Constant(mult)
		elif mult == None: return add.simplify(**methods)
		
		# We have both components, distribute the multiplication into addition.
		
		if isinstance(add, Add):
			addends = []
			
			for a in add.children:
				addends.append((a*mult))
			
			return Add(*addends).simplify(**methods)
			
		else:
			return add.simplify(**methods)*mult.simplify(**methods)

class Pow (Function):
	cardinality = 2
	
	defaultSimplify = lambda f, **methods : f._reduce(**methods)
	
	def __init__(self, a, b):
		Function.__init__(self, '^', a, b, infix = True)
		self.base = a
		self.exp = b

	def _reduce(self, **methods):
		f = self.base.simplify(**methods) ** self.exp.simplify(**methods)
		
		if isinstance(f.base, Constant) and isinstance(f.exp, Constant):
			return Constant(f.base.getValue() ** f.exp.getValue())
			
		elif isinstance(f.exp, Constant):
			v = f.exp.getValue()
			if v == 0:
				return Constant(0)
			elif v == 1:
				return f.base
				
			#Exponentiation.java line 75
			
		return f
		
class Log (Function):
	cardinality = 2
	
	defaultSimplify = lambda f, **methods: f._reduce(**methods)

	def __init__(self, a, b):
		Function.__init__(self, 'log', a, b, prefix = True)
		self.base = a
		self.arg = b
		
	@staticmethod
	def Natural(b):
		return Log(Constant(math.e), b)
		
	def _reduce(self, **methods):
		if isinstance(self.base, Constant) and isinstance(self.arg, Constant):
			return Constant(math.log(self.base.getValue(), self.arg.getValue()))
		else:
			return self

	def __repr__(self):
		if self.base == Constant(math.e):
			return 'ln(%s)' % self.arg
		else:
			return '%s(%s)' % (self.name, ','.join([str(c) for c in self.children]))		

class Cos (Function):
	cardinality = 1
	defaultSimplify = lambda f, **methods : f._reduce(**methods)
	
	def __init__(self, f):
		Function.__init__(self, 'cos', f, prefix = True)

	def _reduce(self, **methods):
		if isinstance(self.children[0], Constant):
			return Constant(math.cos(self.children[0].getValue()))
		else:
			return self

class Sin (Function):
	cardinality = 1
	defaultSimplify = lambda f, **methods : f._reduce(**methods)
	
	def __init__(self, f):
		Function.__init__(self, 'sin', f, prefix = True)

	def _reduce(self, **methods):
		if isinstance(self.children[0], Constant):
			return Constant(math.sin(self.children[0].getValue()))
		else:
			return self

class Tan (Function):
	cardinality = 1
	defaultSimplify = lambda f, **methods : f._reduce(**methods)
	
	def __init__(self, f):
		Function.__init__(self, 'tan', f, prefix = True)

	def _reduce(self, **methods):
		if isinstance(self.children[0], Constant):
			return Constant(math.tan(self.children[0].getValue()))
		else:
			return self

class Sec (Function):
	cardinality = 1
	defaultSimplify = lambda f, **methods : f._reduce(**methods)
	
	def __init__(self, f):
		Function.__init__(self, 'sec', f, prefix = True)

	def _reduce(self, **methods):
		if isinstance(self.children[0], Constant):
			return Constant(math.sec(self.children[0].getValue()))
		else:
			return self
