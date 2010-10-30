import copy

class Function:
	PREFIX = 0
	INFIX = 1
	
	cardinality = 0	
	commutative = False
	associative = False
	
	def __init__(self, name, *children, **attr):
		self.name = name
		self.children = children[:]#[copy.deepcopy(c) for c in children]
		self.fix = Function.PREFIX
		
		if attr.has_key('infix') and attr['infix']:
			self.fix = Function.INFIX
	
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
		
	def expand(self):
		return self
		
	def reduce(self):
		return Add(*[f.reduce() for f in self.children])

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
	
	def __init__(self, a, b):
		Function.__init__(self, '+', a, b, infix = True)
		
	def expand(self):
		n = 0
		others = []
		
		for f in self.children:
			f = f.expand()
			
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
	
	def __init__(self, a, b):
		Function.__init__(self, '*', a, b, infix = True)

	def expand(self):
		dargs = []
		add = None
		mult = None
		num = 1
		
		# Reduce to addition, multiplication, and a constant
		
		for f in self.children:
			f = f.expand()
			
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
		
		if num == 1: num = None
		
		if mult == None and num != None: mult = num
		elif mult != None and num != None: mult *= num
		
		if add == None and mult == None: return Constant(1)
		if add == None: return mult
		if mult == None: return add.expand()
		
		# We have both components, distribute the multiplication into addition.
		
		if isinstance(add, Add):
			addends = []
			
			for a in add.children:
				addends.append((a*mult).expand())
			
			return Add(*addends).expand()
			
		else:
			return add*mult

class Pow (Function):
	cardinality = 2
	def __init__(self, a, b):
		Function.__init__(self, '^', a, b, infix = True)
		
	def __getattr__(self, attr):
		if attr == 'base': return self.children[0]
		elif attr == 'exp': return self.children[1]
		else: return getattr(self, attr)

	def __setattr__(self, attr, value):
		if attr == 'base': self.children[0] = value
		elif attr == 'exp': self.children[1] = value
		else: return setattr(self, attr, value)

	def expand(self):
		f = self.base.expand() ** self.exp.expand()
		
		if isinstance(f.base, Constant) and isinstance(f.exp, Constant):
			return Constant(f.base.getValue() ** f.exp.getValue())
			
		elif isinstance(f.exp, Constant):
			pass
			#Exponentiation.java line 75
	
	def reduce(self):
		pass
		
class Diff (Function):
	cardinality = 2

	def __init__(self, a, b):
		Function.__init__(self, 'diff', a, b, infix = True)

	def __repr__(self):
		return 'd(%s)/d%s' % (self.children[0], self.children[1])

	def expand(self):
		return Diff._diff(self.children[0], self.children[1]).expand()
	
	def reduce(self):
		return Diff._diff(self.children[0], self.children[1]).reduce()
	
	@staticmethod
	def _diff(f, x):
		if not x in f:
			return Constant(0)
			
		if isinstance(f, Add):
			return Add(*[Diff._diff(f, x) for f in f.children])
			
		elif isinstance(f, Mul):
			return f[0]*Diff._diff(f[1], x) + f[1]*Diff._diff(f[0], x)

		elif isinstance(f, Variable):
			if f == x: return Constant(1)
			else: return Constant(0)

		elif isinstance(f, Constant):
			return Constant(0)

		else:
			raise Exception, 'Not differentiable.'
			