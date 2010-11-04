from functions import *

class Diff (Function):
	cardinality = 2

	defaultSimplify = lambda f, **methods : Diff._diff(f.function, f.variable, **methods)

	def __init__(self, a, b):
		Function.__init__(self, 'diff', a, b, infix = True)
		self.function = a
		self.variable = b

	def __repr__(self):
		return 'd(%s)/d%s' % (self.children[0], self.children[1])

	@staticmethod
	def _diff(f, x, **methods):
		if not x in f:
			return Constant(0)
			
		if isinstance(f, Add):
			return Add(*[Diff._diff(f, x) for f in f.children]).simplify(**methods)
			
		elif isinstance(f, Mul):
			return (f[0]*Diff._diff(f[1], x) + f[1]*Diff._diff(f[0], x)).simplify(**methods)

		elif isinstance(f, Variable):
			if f == x: return Constant(1)
			else: return Constant(0)

		elif isinstance(f, Constant):
			return Constant(0)

		elif isinstance(f, Pow):
			b = (x in f.base)
			e = (x in f.exp)

			if b and e:
				return (f * Diff._diff(f.exp, x) * Log.Natural(f) + \
					(f.base ** (f.exp-1)) * f.exp * Diff._diff(f.base, x)).simplify(**methods)
			
			elif b:
				return (f.exp*(f.base**(f.exp-1))*Diff._diff(f.base, x)).simplify(**methods)
			
			elif e:
				return ((f.base**f.exp) * Log(math.e, f.base) * Diff._diff(f.exp, x)).simplify(**methods)

		elif isinstance(f, Log):
			if x in f.base:
				return Diff._diff(Log.Natural(f.arg) / Log.Natural(f.base), x).simplify(**methods)
				
			else:
				return (Diff._diff(f.arg, x) / (f.arg*Log.Natural(f.base))).simplify(**methods)
			
		raise Exception, '\'%s\' is not differentiable.' % f.__class__

class Integration (Function):

	defaultSimplify = lambda f, **methods : Integration._integrate(f.function, f.variable, **methods)

	def __init__(self, f, x, *bounds):
		Function.__init__(self, 'int', [f, x] + bounds, prefix = True)
	
	@staticmethod
	def _integrate(f, **methods):
		return f